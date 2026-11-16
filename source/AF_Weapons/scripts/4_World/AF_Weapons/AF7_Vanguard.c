// Script classes for the AF-7. They behave exactly like the M4A1 (whose script class is
// M4A1_Base), plus the server licence check from AFLicense.c.

class AF7_Vanguard : M4A1_Base
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
}

class AF7_Vanguard_Gold : AF7_Vanguard
{
}
