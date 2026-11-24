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

	//! The front sight (hiddenSelections index 3, "hide_sight") sat in the middle of the scope view, so it
	//! is hidden while the scope is on and shown again when it comes off.
	static const int AF_SIGHT_SELECTION = 3;

	void AF_UpdateFrontSight()
	{
		bool scoped = FindAttachmentBySlotName("weaponOpticsAFStG") != null;
		SetSimpleHiddenSelectionState(AF_SIGHT_SELECTION, !scoped);
	}

	override void EEItemAttached(EntityAI item, string slot_name)
	{
		super.EEItemAttached(item, slot_name);
		AF_UpdateFrontSight();
	}

	override void EEItemDetached(EntityAI item, string slot_name)
	{
		super.EEItemDetached(item, slot_name);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(AF_UpdateFrontSight, 0, false);   // after it is gone
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
