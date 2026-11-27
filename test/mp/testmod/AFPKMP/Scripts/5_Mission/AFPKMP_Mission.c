// Test-only. See config.cpp. Runs on the client; test\mp\run_mp.ps1 reads these log lines.
modded class MissionGameplay
{
	protected bool m_AFTStarted;
	protected int m_AFTBefore;

	override void OnUpdate(float timeslice)
	{
		super.OnUpdate(timeslice);

		if (m_AFTStarted || GetGame().IsDedicatedServer())
			return;
		if (!AFT_Rifle())
			return;
		m_AFTStarted = true;
		Print("[AFPKMP] client has the rifle");
		AFT_Next(0, 10000);
	}

	Weapon_Base AFT_Rifle()
	{
		PlayerBase p = PlayerBase.Cast(GetGame().GetPlayer());
		if (!p || !p.IsAlive())
			return null;
		return Weapon_Base.Cast(p.GetHumanInventory().GetEntityInHands());
	}

	void AFT_Next(int step, int delay)
	{
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFT_Step, delay, false, step);
	}

	//! Rounds left as the PeaceKeeper counts them: magazine plus chamber, -1 with no magazine.
	int AFT_Rounds(Weapon_Base w)
	{
		int mi = w.GetCurrentMuzzle();
		Magazine mag = w.GetMagazine(mi);
		if (!mag)
			return -1;
		int n = mag.GetAmmoCount();
		if (w.IsChamberFull(mi))
			n++;
		return n;
	}

	string AFT_State(Weapon_Base w)
	{
		int mi = w.GetCurrentMuzzle();
		string s = w.GetType() + " rounds " + AFT_Rounds(w).ToString();
		AF_PeaceKeeper pk = AF_PeaceKeeper.Cast(w);
		if (pk)
			s = s + " display " + pk.AFT_Shown().ToString();
		s = s + " mode " + w.GetCurrentModeName(mi) + " burst " + w.GetCurrentModeBurstSize(mi).ToString();
		s = s + " auto " + w.GetCurrentModeAutoFire(mi).ToString();
		return s;
	}

	void AFT_Hold(Weapon_Base w, int ms, string tag)
	{
		m_AFTBefore = AFT_Rounds(w);
		Print("[AFPKMP] before " + tag + ": " + AFT_State(w));
		Print("[AFPKMP] HOLD " + ms.ToString() + " " + tag);
	}

	void AFT_Fired(Weapon_Base w, string tag)
	{
		int fired = m_AFTBefore - AFT_Rounds(w);
		Print("[AFPKMP] RESULT " + tag + " fired " + fired.ToString() + ": " + AFT_State(w));
	}

	void AFT_HoldAim()
	{
		PlayerBase p = PlayerBase.Cast(GetGame().GetPlayer());
		if (p && !p.IsInIronsights())
			p.SetIronsights(true);
	}

	void AFT_Ground(PlayerBase p, Weapon_Base held)
	{
		// The rifles the server put on the ground: their counters come from synced state alone.
		array<Object> near = new array<Object>;
		GetGame().GetObjectsAtPosition(p.GetPosition(), 12, near, null);
		foreach (Object o : near)
		{
			AF_PeaceKeeper g = AF_PeaceKeeper.Cast(o);
			if (g && g != held)
			{
				bool stock = g.FindAttachmentBySlotName("weaponButtstockSCAR") != null;
				Print("[AFPKMP] GROUND rifle: " + AFT_State(g) + " stock " + stock.ToString());
			}
		}
	}

	void AFT_Step(int step)
	{
		PlayerBase p = PlayerBase.Cast(GetGame().GetPlayer());
		Weapon_Base w = AFT_Rifle();
		if (!p || !w)
		{
			Print("[AFPKMP] FAILED: no rifle in hands at step " + step.ToString());
			Print("[AFPKMP] CLIENT DONE");
			return;
		}

		if (step == 0)
		{
			bool stock = w.FindAttachmentBySlotName("weaponButtstockSCAR") != null;
			Print("[AFPKMP] start: " + AFT_State(w));
			Print("[AFPKMP] stock fitted: " + stock.ToString());
			GetGame().GetUIManager().CloseAll();
			p.GetInputController().OverrideRaise(HumanInputControllerOverrideType.ENABLED, true);
			AFT_Next(1, 4000);
		}
		else if (step == 1)			// the first click may only give the window the mouse
		{
			AFT_Hold(w, 150, "warmup");
			AFT_Next(2, 3000);
		}
		else if (step == 2)
		{
			AFT_Fired(w, "warmup");
			AFT_Hold(w, 1500, "semi");
			AFT_Next(3, 4500);
		}
		else if (step == 3)
		{
			AFT_Fired(w, "semi");
			p.GetWeaponManager().SetNextMuzzleMode();
			AFT_Next(4, 2500);
		}
		else if (step == 4)
		{
			AFT_Hold(w, 1500, "burst");
			AFT_Next(5, 4500);
		}
		else if (step == 5)
		{
			AFT_Fired(w, "burst");
			AFT_Hold(w, 1500, "burst2");
			AFT_Next(6, 4500);
		}
		else if (step == 6)
		{
			AFT_Fired(w, "burst2");
			p.GetWeaponManager().SetNextMuzzleMode();
			AFT_Next(7, 2500);
		}
		else if (step == 7)
		{
			AFT_Hold(w, 500, "full");
			AFT_Next(8, 4000);
		}
		else if (step == 8)
		{
			AFT_Fired(w, "full");
			GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFT_HoldAim, 100, true);
			AFT_Next(9, 4000);
		}
		else if (step == 9)
		{
			Print("[AFPKMP] in iron sights: " + p.IsInIronsights().ToString());
			Print("[AFPKMP] SHOT iron");
			AFT_Next(10, 3000);
		}
		else
		{
			GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).Remove(this.AFT_HoldAim);
			p.SetIronsights(false);
			AFT_Ground(p, w);
			Print("[AFPKMP] end: " + AFT_State(w));
			Print("[AFPKMP] CLIENT DONE");
		}
	}
}
