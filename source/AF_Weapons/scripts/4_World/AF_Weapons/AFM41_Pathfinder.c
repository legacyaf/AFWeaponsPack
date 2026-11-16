// Script class for the AF M41 Pathfinder. It behaves exactly like the vanilla Mosin 91/30
// (script class Mosin9130_Base), plus the server licence check from AFLicense.c.

class AFM41_Pathfinder : Mosin9130_Base
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

class AFM41_Pathfinder_Gold : AFM41_Pathfinder
{
}
