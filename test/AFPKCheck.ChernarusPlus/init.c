// Quick checks on The PeaceKeeper, after the first in-game test (2026-11-26):
//  - the burst size of each fire mode (the burst itself is driven by the player holding the trigger);
//  - where the fitted UniversalLight sits on the rifle (it attached but did not show);
//  - the view down the gold iron sights from the player's own first-person camera (no still camera).
// Start it with: test\run_test.ps1 -Mission AFPKCheck.ChernarusPlus

PlayerBase g_P;
Weapon_Base g_W;

string V(vector v)
{
	return string.Format("%1 %2 %3", v[0].ToString(), v[1].ToString(), v[2].ToString());
}

void main()
{
	GetGame().GetWorld().SetDate(2026, 6, 15, 12, 0);
	Weather weather = GetGame().GetWeather();
	weather.GetOvercast().Set(0, 0, 0);
	weather.GetFog().Set(0, 0, 0);
	vector stand = "4660 0 10330";
	stand[1] = GetGame().SurfaceY(stand[0], stand[2]);
	g_P = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", stand, 0, "NONE"));
	GetGame().SelectPlayer(NULL, g_P);
	g_P.GetInventory().CreateInInventory("TShirt_Green");
	g_W = Weapon_Base.Cast(g_P.GetHumanInventory().CreateInHands("AF_PeaceKeeper"));
	g_W.GetInventory().CreateAttachment("AF_PeaceKeeperStock");
	g_W.SpawnAmmo("Mag_SCARH_20Rnd", WeaponWithAmmoFlags.CHAMBER | WeaponWithAmmoFlags.MAX_CAPACITY_MAG);
	TStringArray more = {"UniversalLight"};
	foreach (string an : more)
		Print("[AFCheck] fitted " + an + " " + (g_W.GetInventory().CreateAttachment(an) != null).ToString());
}

class CustomMission: MissionGameplay
{
	override void OnInit()
	{
		super.OnInit();
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFInfo, 14000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFRaise, 15000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFAim, 18000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFShot, 22000, false, "pk_iron_1");
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFShot, 25000, false, "pk_iron_2");
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFQuit, 28000, false);
	}

	void AFInfo()
	{
		for (int m = 0; m < 3; m++)
		{
			Print("[AFCheck] mode " + g_W.GetCurrentMode(0).ToString() + " burst size " + g_W.GetCurrentModeBurstSize(0).ToString());
			g_W.SetNextMuzzleMode(0);
		}
		for (int i = 0; i < g_W.GetInventory().AttachmentCount(); i++)
		{
			EntityAI a = g_W.GetInventory().GetAttachmentFromIndex(i);
			vector o = g_W.WorldToModel(a.GetPosition());
			vector fwd = g_W.WorldToModel(a.ModelToWorld("0 0 1")) - o;
			vector up = g_W.WorldToModel(a.ModelToWorld("0 1 0")) - o;
			Print("[AFCheck] " + a.GetType() + " at " + V(o) + " dir " + V(fwd) + " up " + V(up));
		}
	}

	void AFRaise()
	{
		g_P.GetInputController().OverrideRaise(HumanInputControllerOverrideType.ENABLED, true);
	}

	void AFAim()
	{
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFHoldAim, 100, true);
	}

	void AFHoldAim()
	{
		if (!g_P.IsInIronsights())
			g_P.SetIronsights(true);
	}

	void AFShot(string name)
	{
		Print("[AFCheck] ironsights=" + g_P.IsInIronsights().ToString() + " camera " + V(g_W.WorldToModel(GetGame().GetCurrentCameraPosition())));
		Print("[AFTest] screenshot " + name);
	}

	void AFQuit()
	{
		GetGame().RequestExit(0);
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
