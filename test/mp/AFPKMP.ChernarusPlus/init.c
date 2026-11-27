// Server side of test\mp\run_mp.ps1: Bohemia's stock Chernarus mission with a fixed spawn. The player
// gets a PeaceKeeper with its AF stock, a full magazine and a chambered round; two more PeaceKeepers
// lie on the ground beside them, one with 7 rounds in its magazine and one with no magazine. The
// server logs the held rifle's rounds every second, to compare with the client's counter.

PlayerBase g_AFTPlayer;

void main()
{
	Hive ce = CreateHive();
	if (ce)
		ce.InitOffline();
	GetGame().GetWorld().SetDate(2026, 6, 15, 12, 0);
	Print("[AFPKMP] server ready");
}

class CustomMission: MissionServer
{
	override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
	{
		vector at = "4660 0 10330";
		at[1] = GetGame().SurfaceY(at[0], at[2]);
		Entity playerEnt = GetGame().CreatePlayer(identity, characterName, at, 0, "NONE");
		Class.CastTo(m_player, playerEnt);
		GetGame().SelectPlayer(identity, m_player);
		return m_player;
	}

	override void StartingEquipSetup(PlayerBase player, bool clothesChosen)
	{
		g_AFTPlayer = player;
		string rifle = "AF_PeaceKeeper";
		string asked;
		if (GetGame().CommandlineGetParam("afrifle", asked) && asked != "")
			rifle = asked;			// a vanilla rifle as the control: run_mp.ps1 -Rifle SCAR
		Weapon_Base w = Weapon_Base.Cast(player.GetHumanInventory().CreateInHands(rifle));
		if (!w)
		{
			Print("[AFPKMP] FAILED: could not create the rifle in hands");
			return;
		}
		if (rifle == "AF_PeaceKeeper")
			w.GetInventory().CreateAttachment("AF_PeaceKeeperStock");
		else
			w.GetInventory().CreateAttachment("SCAR_StockBttstck");
		w.SpawnAmmo("Mag_SCARH_20Rnd", WeaponWithAmmoFlags.CHAMBER | WeaponWithAmmoFlags.MAX_CAPACITY_MAG);
		Print("[AFPKMP] server gave the rifle");

		vector p = player.GetPosition();
		Weapon_Base a = Weapon_Base.Cast(GetGame().CreateObjectEx("AF_PeaceKeeper", Vector(p[0] + 1.5, p[1], p[2] + 1.0), ECE_PLACE_ON_SURFACE));
		if (a)
		{
			Magazine m = Magazine.Cast(a.GetInventory().CreateAttachment("Mag_SCARH_20Rnd"));
			if (m)
				m.ServerSetAmmoCount(7);
			a.SetSynchDirty();
		}
		GetGame().CreateObjectEx("AF_PeaceKeeper", Vector(p[0] + 1.5, p[1], p[2] - 1.0), ECE_PLACE_ON_SURFACE);

		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFT_Log, 1000, true);
	}

	void AFT_Log()
	{
		if (!g_AFTPlayer)
			return;
		Weapon_Base w = Weapon_Base.Cast(g_AFTPlayer.GetHumanInventory().GetEntityInHands());
		if (!w)
		{
			Print("[AFPKMP] server: no rifle in hands");
			return;
		}
		int mi = w.GetCurrentMuzzle();
		Magazine mag = w.GetMagazine(mi);
		int n = -1;
		if (mag)
			n = mag.GetAmmoCount();
		Print("[AFPKMP] server magazine " + n.ToString() + " chamber " + w.IsChamberFull(mi).ToString() + " mode " + w.GetCurrentModeName(mi));
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
