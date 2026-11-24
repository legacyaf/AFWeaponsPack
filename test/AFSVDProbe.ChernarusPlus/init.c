// Probe mission: reads the vanilla SVD's frame from the running game, for the AF M107A1 (which
// inherits the SVD). Uses only the public script API on a spawned SVD; nothing is extracted from
// the game files. Logs, in the SVD's model space (metres):
//   - its memory points (muzzle, barrel end, eye, case ejection);
//   - where its magazine and PSO-1 scope sit (position and axes of each attachment);
//   - where the player's hands hold it, at rest and raised (aimed).
// Then quits. Start it with: test\run_test.ps1 -Mission AFSVDProbe.ChernarusPlus

PlayerBase g_P;
Weapon_Base g_W;

string V(vector v)
{
	return string.Format("%1 %2 %3", v[0].ToString(), v[1].ToString(), v[2].ToString());
}

void LogFrame(string tag)
{
	if (!g_W)
	{
		Print("[AFProbe] FAILED no weapon");
		return;
	}
	TStringArray mem = {"usti hlavne", "konec hlavne", "eye", "nabojnicestart", "nabojniceend", "bolt_axis", "trigger_axis", "magazine_axis", "magazine_axis2"};
	foreach (string m : mem)
	{
		if (g_W.MemoryPointExists(m))
			Print("[AFProbe] " + tag + " mem " + m + " = " + V(g_W.GetMemoryPointPos(m)));
		else
			Print("[AFProbe] " + tag + " mem " + m + " MISSING");
	}
	for (int i = 0; i < g_W.GetInventory().AttachmentCount(); i++)
	{
		EntityAI a = g_W.GetInventory().GetAttachmentFromIndex(i);
		vector o = g_W.WorldToModel(a.GetPosition());
		vector fwd = g_W.WorldToModel(a.ModelToWorld("0 0 1")) - o;
		vector up = g_W.WorldToModel(a.ModelToWorld("0 1 0")) - o;
		Print("[AFProbe] " + tag + " attachment " + a.GetType() + " at " + V(o) + " dir " + V(fwd) + " up " + V(up));
	}
	if (g_P)
	{
		TStringArray hb = {"RightHand", "LeftHand", "RightHandIndex1", "LeftHandIndex1", "Head", "Spine3"};
		foreach (string h : hb)
		{
			int hi = g_P.GetBoneIndexByName(h);
			if (hi >= 0)
				Print("[AFProbe] " + tag + " hand " + h + " = " + V(g_W.WorldToModel(g_P.GetBonePositionWS(hi))));
		}
	}
	vector box[2];
	g_W.GetCollisionBox(box);
	Print("[AFProbe] " + tag + " collision box " + V(box[0]) + " .. " + V(box[1]));
}

void main()
{
	GetGame().GetWorld().SetDate(2026, 6, 15, 12, 0);
	vector stand = "4660 0 10330";
	stand[1] = GetGame().SurfaceY(stand[0], stand[2]);
	g_P = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", stand, 0, "NONE"));
	GetGame().SelectPlayer(NULL, g_P);
	g_P.GetInventory().CreateInInventory("TShirt_Green");
	g_W = Weapon_Base.Cast(g_P.GetHumanInventory().CreateInHands("SVD"));
	if (g_W)
	{
		g_W.SpawnAmmo("Mag_SVD_10Rnd", WeaponWithAmmoFlags.CHAMBER | WeaponWithAmmoFlags.MAX_CAPACITY_MAG);
		g_W.GetInventory().CreateAttachment("PSO1Optic");
	}
	Print("[AFProbe] spawned SVD " + (g_W != null).ToString());
}

class CustomMission: MissionGameplay
{
	override void OnInit()
	{
		super.OnInit();
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFRest, 15000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFRaise, 18000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFRaised, 22000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFQuit, 24000, false);
	}

	void AFRest()
	{
		LogFrame("rest");
	}

	void AFRaise()
	{
		g_P.GetInputController().OverrideRaise(HumanInputControllerOverrideType.ENABLED, true);
		Print("[AFProbe] raising");
	}

	void AFRaised()
	{
		LogFrame("raised");
	}

	void AFQuit()
	{
		Print("[AFProbe] done");
		GetGame().RequestExit(0);
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
