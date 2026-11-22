// Script classes for the AF StG 44. It behaves exactly like the vanilla AKM (script class
// AKM), plus the server licence check from AFLicense.c.

class AF_StG44 : AKM
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

	//! Debug menu "Spawn Ground Special": with its own magazine and its own scope.
	override void OnDebugSpawn()
	{
		GetInventory().CreateInInventory("AF_ZF4Optic");
		SpawnAttachedMagazine("Mag_AFStG44_30Rnd");
	}
}

class AF_StG44_Gold : AF_StG44
{
}
