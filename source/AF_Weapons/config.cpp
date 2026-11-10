////////////////////////////////////////////////////////////////////
// Allied Forces Weapons Pack
//
// AF-7 "Vanguard" - original Allied Forces assault rifle, 5.56x45.
//
// It inherits from the vanilla M4A1. That gives it the M4's
// animations, sounds, recoil, fire modes and STANAG magazines, so we
// only need to supply the model and textures.
//
// HOW TO SWITCH TO YOUR OWN MODEL
//   Phase 1 (now): the custom-model lines below are commented out, so
//                  the Vanguard shows up with the M4 model. Use this to
//                  check that the mod, loot and signing all work.
//   Phase 2:       when af7_vanguard.p3d exists in
//                  P:\AF_Weapons\af7_vanguard\, remove the // in front
//                  of every line marked [MODEL]. Then rebuild.
////////////////////////////////////////////////////////////////////

class CfgPatches
{
	class AF_Weapons
	{
		units[] = {};
		weapons[] = {"AF7_Vanguard"};
		requiredVersion = 0.1;
		requiredAddons[] = {"DZ_Data", "DZ_Weapons_Firearms"};
	};
};

class CfgMods
{
	class AF_WeaponsPack
	{
		dir = "AF_WeaponsPack";
		name = "Allied Forces Weapons Pack";
		author = "Allied Forces";
		type = "mod";
		version = "0.1.0";
		dependencies[] = {};
	};
};

class CfgWeapons
{
	class M4A1;

	class AF7_Vanguard: M4A1
	{
		scope = 2;
		displayName = "AF-7 Vanguard";
		descriptionShort = "An Allied Forces assault rifle in 5.56x45mm, built for front-line squads. It has a long, slotted handguard, a skeleton stock and a full-length top rail. It takes standard STANAG magazines.";
		weight = 3200;

		// Slightly better handling than a stock M4 (lower = less recoil/sway)
		recoilModifier[] = {0.9, 0.9, 0.9};
		swayModifier[] = {1.7, 1.7, 1.0};

		// ---------------- [MODEL] custom model (Phase 2) ----------------
		// model = "\AF_Weapons\af7_vanguard\af7_vanguard.p3d";              // [MODEL]
		// The stock and handguard are part of the model, so only rail optics,
		// muzzle devices and a flashlight attach. VERIFY these slot names
		// against the vanilla M4A1 attachments[] list (GUIDE step 0).
		// attachments[] = {"weaponOptics", "weaponMuzzleM4", "weaponFlashlight"}; // [MODEL]
		// hiddenSelections[] = {"camo"};                                     // [MODEL]
		// hiddenSelectionsTextures[] = {"AF_Weapons\af7_vanguard\data\af7_body_co.paa"};   // [MODEL]
		// hiddenSelectionsMaterials[] = {"AF_Weapons\af7_vanguard\data\af7_body.rvmat"};   // [MODEL]
	};
};
