// Script classes for the AF MP40. It behaves exactly like the vanilla UMP-45 (script class
// UMP45_Base), plus the server licence check from AFLicense.c.

class AF_MP40 : UMP45_Base
{
	override void EEInit()
	{
		super.EEInit();

		if (GetGame().IsDedicatedServer())
		{
			AFLicense.Start();
			GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(AF_CheckLicense, 5000, false);
		}
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

	//! Debug menu "Spawn Ground Special": with its own magazine and a suppressor.
	override void OnDebugSpawn()
	{
		GetInventory().CreateInInventory("PistolSuppressor");
		SpawnAttachedMagazine("Mag_AFMP40_32Rnd");
	}
}

class AF_MP40_Gold : AF_MP40
{
}
