// Script classes for the AF P08. It behaves exactly like the vanilla P1 (script class
// P1_Base), plus the server licence check from AFLicense.c.

class AF_P08 : P1_Base
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

	//! Debug menu "Spawn Ground Special": with its own magazine.
	override void OnDebugSpawn()
	{
		SpawnAttachedMagazine("Mag_AFP08_8Rnd");
	}
}

class AF_P08_Gold : AF_P08
{
}
