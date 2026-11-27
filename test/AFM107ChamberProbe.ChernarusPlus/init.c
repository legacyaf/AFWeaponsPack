// Probe mission: does the AF M107A1 chamber a round from its magazine? Owner, 2026-11-26: "the 50 cal is
// not reloading ammo in the chamber". Runs the same steps on the AF M107A1 and, as the control, the
// vanilla SVD it inherits from: an empty rifle in the hands, a full magazine attached through the
// player's weapon manager (as a reload), fired empty, reloaded with a full one, and a loose round loaded into the empty chamber, logging the
// chamber and magazine after each step.
// Start it with: test\run_test.ps1 -Mission AFM107ChamberProbe.ChernarusPlus

PlayerBase g_P;
Weapon_Base g_W;
Magazine g_M;
Magazine g_M2;
Magazine g_Loose;
Weapon_Base g_W2;
ref TStringArray g_Rifles = {"AF_M107A1", "SVD"};
ref TStringArray g_Mags = {"Mag_AFM107_10Rnd", "Mag_SVD_10Rnd"};
ref TStringArray g_Ammo = {"Ammo_AF50BMG", "Ammo_762x54"};
int g_I;
int g_Step;

void State(string tag)
{
	if (!g_W)
	{
		Print("[AFChamber] " + tag + " no weapon");
		return;
	}
	Magazine m = g_W.GetMagazine(0);
	int n = -1;
	if (m)
		n = m.GetAmmoCount();
	Print("[AFChamber] " + g_Rifles[g_I] + " " + tag + ": chamber empty=" + g_W.IsChamberEmpty(0).ToString() + " full=" + g_W.IsChamberFull(0).ToString() + " firedout=" + g_W.IsChamberFiredOut(0).ToString() + " mag=" + (m != null).ToString() + " rounds=" + n.ToString() + " cartridge=" + g_W.GetChamberedCartridgeMagazineTypeName(0));
}

void Setup()
{
	string rifle = g_Rifles[g_I];
	TStringArray arr = new TStringArray;
	GetGame().ConfigGetTextArray("CfgWeapons " + rifle + " chamberableFrom", arr);
	Print("[AFChamber] " + rifle + " chamberableFrom " + arr.ToString());
	string ammo;
	GetGame().ConfigGetText("CfgMagazines " + g_Mags[g_I] + " ammo", ammo);
	arr.Clear();
	GetGame().ConfigGetTextArray("CfgMagazines " + g_Mags[g_I] + " ammoItems", arr);
	string pile;
	GetGame().ConfigGetText("CfgAmmo " + ammo + " spawnPileType", pile);
	Print("[AFChamber] " + g_Mags[g_I] + " ammo " + ammo + " ammoItems " + arr.ToString() + " spawnPileType " + pile);
	g_W = Weapon_Base.Cast(g_P.GetHumanInventory().CreateInHands(rifle));
	g_M = Magazine.Cast(g_P.GetInventory().CreateInInventory(g_Mags[g_I]));
	if (g_M)
		g_M.ServerSetAmmoCount(2);          // two rounds: fired empty quickly
	g_M2 = Magazine.Cast(g_P.GetInventory().CreateInInventory(g_Mags[g_I]));
	if (g_M2)
		g_M2.ServerSetAmmoCount(g_M2.GetAmmoMax());
	Print("[AFChamber] " + rifle + " spawned " + (g_W != null).ToString() + ", magazine " + (g_M != null).ToString() + " CanChamberFromMag=" + g_W.CanChamberFromMag(0, g_M).ToString() + " CanAttachMagazine=" + g_W.CanAttachMagazine(0, g_M).ToString());
	State("empty");
}

void main()
{
	GetGame().GetWorld().SetDate(2026, 6, 15, 12, 0);
	vector stand = "4660 0 10330";
	stand[1] = GetGame().SurfaceY(stand[0], stand[2]);
	g_P = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", stand, 0, "NONE"));
	GetGame().SelectPlayer(NULL, g_P);
	g_P.GetInventory().CreateAttachment("TacticalShirt_Black");
	g_P.GetInventory().CreateAttachment("CargoPants_Black");
}

class CustomMission: MissionGameplay
{
	override void OnInit()
	{
		super.OnInit();
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFStep, 12000, true);
	}

	// One step every 4 seconds per rifle (after a 12 s start): set up, reload, fire three times, then the next rifle.
	void AFStep()
	{
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).Remove(this.AFStep);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFStep, 4000, true);
		if (g_I >= g_Rifles.Count())
		{
			Print("[AFChamber] done");
			GetGame().RequestExit(0);
			return;
		}
		switch (g_Step)
		{
			case 0:
				Setup();
				break;
			case 1:
				Print("[AFChamber] " + g_Rifles[g_I] + " reload (2-round magazine): AttachMagazine=" + g_P.GetWeaponManager().AttachMagazine(g_M).ToString());
				break;
			case 2:
				State("after reload");
				g_P.GetWeaponManager().Fire(g_W);
				break;
			case 3:
				State("after shot 1");
				g_P.GetWeaponManager().Fire(g_W);
				break;
			case 4:
				State("after shot 2 (magazine empty)");
				g_P.GetWeaponManager().Fire(g_W);
				break;
			case 5:
				State("after shot 3 (dry)");
				Print("[AFChamber] " + g_Rifles[g_I] + " swap to a full magazine: CanSwap=" + g_P.GetWeaponManager().CanSwapMagazine(g_W, g_M2).ToString() + " Swap=" + g_P.GetWeaponManager().SwapMagazine(g_M2).ToString());
				break;
			case 6:
				State("after reload of the emptied rifle");
				GetGame().ObjectDelete(g_W);
				break;
			case 7:
				// A loose round straight into the chamber of an empty rifle, no magazine.
				g_W = Weapon_Base.Cast(g_P.GetHumanInventory().CreateInHands(g_Rifles[g_I]));
				g_Loose = Magazine.Cast(g_P.GetInventory().CreateInInventory(g_Ammo[g_I]));
				if (g_Loose)
					g_Loose.ServerSetAmmoCount(5);
				Print("[AFChamber] " + g_Rifles[g_I] + " loose round: CanLoadBullet=" + g_P.GetWeaponManager().CanLoadBullet(g_W, g_Loose).ToString() + " LoadBullet=" + g_P.GetWeaponManager().LoadBullet(g_Loose).ToString());
				break;
			case 8:
				State("after loading a loose round");
				GetGame().ObjectDelete(g_W);
				g_Step = -1;
				g_I++;
				break;
		}
		g_Step++;
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
