// Script class for The PeaceKeeper (docs/AF_SCAR.md).
//
// AF_PeaceKeeper behaves like the vanilla SCAR-H (script class SCARH_Base: its handling, folding-sight
// rules and recoil), plus:
//  - the server licence check from AFLicense.c;
//  - its AF stock, fitted when the loot economy spawns the rifle (it can be taken off, and vanilla SCAR
//    stocks fit);
//  - the live round counter: the display (hidden selection camo4) shows the rounds left, magazine plus
//    chamber, "--" with no magazine. Each machine reads the weapon's synced magazine and chamber state
//    (so other players' rifles show the right count too) and swaps the display's texture when it changes.

class AF_PeaceKeeper : SCARH_Base
{
	static const int AF_COUNTER_SELECTION = 4;            // camo4 in config.cpp
	static const int AF_COUNTER_MAX = 21;                 // 20 in the magazine, 1 in the chamber
	static const string AF_COUNTER_PATH = "AF_Weapons/afpk/data/afpk_count_";

	protected int m_AFShown = -2;                         // the count on the display (-1: "--", -2: not set)

	override void EEInit()
	{
		super.EEInit();

		if (!GetGame().IsDedicatedServer())
			GetGame().GetCallQueue(CALL_CATEGORY_GUI).CallLater(AF_UpdateCounter, 250, true);

		if (GetGame().IsDedicatedServer())
		{
			AFLicense.Start();
			GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(AF_CheckLicense, 5000, false);
		}
	}

	override void EEDelete(EntityAI parent)
	{
		GetGame().GetCallQueue(CALL_CATEGORY_GUI).Remove(AF_UpdateCounter);
		super.EEDelete(parent);
	}

	//! A rifle spawned by the loot economy comes with the AF stock. Only then: a stock taken off stays off
	//! across restarts, and a vanilla SCAR stock can take its place.
	override void EEOnCECreate()
	{
		super.EEOnCECreate();
		AF_FitStock();
	}

	void AF_FitStock()
	{
		if (!FindAttachmentBySlotName("weaponButtstockSCAR"))
			GetInventory().CreateAttachment("AF_PeaceKeeperStock");
	}

	//! Rounds left: the attached magazine's count plus the chambered round; -1 with no magazine.
	int AF_RoundsLeft()
	{
		int mi = GetCurrentMuzzle();
		Magazine mag = GetMagazine(mi);
		if (!mag)
			return -1;
		int n = mag.GetAmmoCount();
		if (IsChamberFull(mi))
			n++;
		return Math.Clamp(n, 0, AF_COUNTER_MAX);
	}

	//! Four times a second on each player's machine: swap the display's texture when the count changes.
	void AF_UpdateCounter()
	{
		int n = AF_RoundsLeft();
		if (n == m_AFShown)
			return;
		m_AFShown = n;
		string tex;
		if (n < 0)
			tex = AF_COUNTER_PATH + "none_co.paa";
		else
			tex = AF_COUNTER_PATH + n.ToString() + "_co.paa";
		SetObjectTexture(AF_COUNTER_SELECTION, tex);
	}

	//! Runs every 5 seconds until the licence is known. Deletes the weapon on an unlicensed server.
	void AF_CheckLicense()
	{
		if (AFLicense.IsOK())
			return;

		if (AFLicense.IsDenied())
		{
			GetGame().ObjectDelete(this);
			return;
		}

		AFLicense.Poll();
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(AF_CheckLicense, 5000, false);
	}

	//! Debug menu "Spawn Ground Special": with its AF stock and a full magazine.
	override void OnDebugSpawn()
	{
		AF_FitStock();
		SpawnAttachedMagazine("Mag_SCARH_20Rnd");
	}
}
