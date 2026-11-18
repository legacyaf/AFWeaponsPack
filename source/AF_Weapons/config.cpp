////////////////////////////////////////////////////////////////////
// Allied Forces Weapons Pack
//
// AF-7 "Vanguard"    - original Allied Forces assault rifle, 5.56x45 / .308.
// AF M41 "Pathfinder" - WW2-style bolt-action sniper rifle, 7.62x54R (inherits the Mosin 91/30).
//
// Each rifle inherits a vanilla weapon (M4A1, Mosin 91/30). That gives it that
// weapon's animations, sounds, recoil and fire modes, so we only need to supply
// the model and textures.
//
// CUSTOM MODEL
//   Phase 2 (now): the lines marked [MODEL] are active, so the Vanguard
//                  uses af7_vanguard\af7_vanguard.p3d and its textures.
//   To go back to the plain M4 model (Phase 1, handy for checking that
//   the mod, loot and signing work): put // in front of every line
//   marked [MODEL], then rebuild.
////////////////////////////////////////////////////////////////////

class CfgPatches
{
	class AF_Weapons
	{
		units[] = {};
		weapons[] = {"AF7_Vanguard", "AF7_Vanguard_Gold", "AFM41_Pathfinder", "AFM41_Pathfinder_Gold"};
		requiredVersion = 0.1;
		requiredAddons[] = {"DZ_Data", "DZ_Scripts", "DZ_Weapons_Firearms", "DZ_Weapons_Firearms_M4", "DZ_Weapons_Firearms_FAL", "DZ_Weapons_Firearms_MosinNagant"};
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
		version = "0.8.3";
		dependencies[] = {"World"};

		// Scripts: the AF-7 script classes and the server licence check (scripts/4_World).
		class defs
		{
			class worldScriptModule
			{
				value = "";
				files[] = {"AF_Weapons/scripts/4_World"};
			};
		};
	};
};

class CfgWeapons
{
	class M4A1;
	class Mosin9130;

	class AF7_Vanguard: M4A1
	{
		scope = 2;
		displayName = "AF-7 Vanguard";
		descriptionShort = "An Allied Forces multi-calibre assault rifle, built for front-line squads. It has a long, slotted handguard, a skeleton stock and a full-length top rail. It feeds 5.56x45mm from STANAG magazines or .308 Winchester from LAR magazines.";
		weight = 3200;

		// Slightly better handling than a stock M4 (lower = less recoil/sway)
		recoilModifier[] = {0.9, 0.9, 0.9};
		swayModifier[] = {1.7, 1.7, 1.0};

		// Two ammo types. The magazine that is loaded decides what the rifle fires:
		//   5.56x45  - every magazine the vanilla M4A1 takes (STANAG, CMAG)
		//   .308 Win - the vanilla LAR (FAL) 20-round magazine
		// A loose round of either calibre can also be chambered by hand.
		// Damage and ballistics come from the ammo; sounds and recoil stay the M4's.
		chamberableFrom[] =
		{
			"Ammo_556x45", "Ammo_556x45Tracer",
			"Ammo_308Win", "Ammo_308WinTracer"
		};
		magazines[] =
		{
			"Mag_STANAG_30Rnd", "Mag_STANAGCoupled_30Rnd", "Mag_STANAG_60Rnd",
			"Mag_CMAG_10Rnd", "Mag_CMAG_20Rnd", "Mag_CMAG_30Rnd", "Mag_CMAG_40Rnd",
			"Mag_CMAG_10Rnd_Green", "Mag_CMAG_20Rnd_Green", "Mag_CMAG_30Rnd_Green", "Mag_CMAG_40Rnd_Green",
			"Mag_CMAG_10Rnd_Black", "Mag_CMAG_20Rnd_Black", "Mag_CMAG_30Rnd_Black", "Mag_CMAG_40Rnd_Black",
			"Mag_FAL_20Rnd"
		};

		// ---------------- [MODEL] custom model (Phase 2) ----------------
		// Slot names confirmed from vanilla M4A1. The stock and handguard are
		// built into the Vanguard, so the M4 stock/handguard slots are left out.
		// The M4's wrap, bayonet and bipod slots are left out too: af7_vanguard.p3d
		// only has proxies for an optic, a flashlight, a suppressor and the magazine.
		model = "\AF_Weapons\af7_vanguard\af7_vanguard.p3d";              // [MODEL]
		attachments[] = {"weaponOptics", "weaponFlashlight", "weaponMuzzleM4"}; // [MODEL]
		hiddenSelections[] = {"camo", "hide_barrel"};   // [MODEL] the muzzle brake is retextured with the body
		hiddenSelectionsTextures[] = {"AF_Weapons\af7_vanguard\data\af7_body_co.paa", "AF_Weapons\af7_vanguard\data\af7_body_co.paa"};   // [MODEL]
		hiddenSelectionsMaterials[] = {"AF_Weapons\af7_vanguard\data\af7_body.rvmat", "AF_Weapons\af7_vanguard\data\af7_body.rvmat"};   // [MODEL]

		// Iron sights: no depth-of-field blur when aiming. The M4 default blurred the whole view
		// through this rifle's low backup sights. The other values are the M4's.
		PPDOFProperties[] = {0, 0.6, 50, 200, 4, 10};
		// (hiddenSelections[] = {"camo"}, simpleHiddenSelections[] = {"hide_barrel"} and
		//  WeaponLength = 0.78 are inherited from the M4. The model has both selections,
		//  and its muzzle is the same distance from the model origin as the M4's.)
		//
		// Damage looks, same thresholds as the vanilla M4: pristine/worn use the
		// normal material, damaged/badly damaged add scratches, ruined adds the
		// destruction overlay.
		class DamageSystem                                                  // [MODEL]
		{                                                                   // [MODEL]
			class GlobalHealth                                                 // [MODEL]
			{                                                                  // [MODEL]
				class Health                                                   // [MODEL]
				{                                                              // [MODEL]
					hitpoints = 200;                                           // [MODEL]
					healthLevels[] =                                           // [MODEL]
					{                                                          // [MODEL]
						{1.0, {"AF_Weapons\af7_vanguard\data\af7_body.rvmat"}},            // [MODEL]
						{0.7, {"AF_Weapons\af7_vanguard\data\af7_body.rvmat"}},            // [MODEL]
						{0.5, {"AF_Weapons\af7_vanguard\data\af7_body_damage.rvmat"}},     // [MODEL]
						{0.3, {"AF_Weapons\af7_vanguard\data\af7_body_damage.rvmat"}},     // [MODEL]
						{0.0, {"AF_Weapons\af7_vanguard\data\af7_body_destruct.rvmat"}}    // [MODEL]
					};                                                         // [MODEL]
				};                                                             // [MODEL]
			};                                                                 // [MODEL]
		};                                                                  // [MODEL]
	};

	// Gold floral skin: the pattern, colours and material settings come from the
	// old Allied Forces R700 chassis texture. Same rifle, different textures.
	// Not in the loot tables (server/af_ce); spawn it with an admin tool or add it there.
	class AF7_Vanguard_Gold: AF7_Vanguard
	{
		scope = 2;
		displayName = "AF-7 Vanguard (Gold)";
		descriptionShort = "An Allied Forces AF-7 Vanguard with gold floral furniture on black. It feeds 5.56x45mm from STANAG magazines or .308 Winchester from LAR magazines.";
		hiddenSelectionsTextures[] = {"AF_Weapons\af7_vanguard\data\af7_body_gold_co.paa", "AF_Weapons\af7_vanguard\data\af7_body_gold_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\af7_vanguard\data\af7_body_gold.rvmat", "AF_Weapons\af7_vanguard\data\af7_body_gold.rvmat"};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 200;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\af7_vanguard\data\af7_body_gold.rvmat"}},
						{0.7, {"AF_Weapons\af7_vanguard\data\af7_body_gold.rvmat"}},
						{0.5, {"AF_Weapons\af7_vanguard\data\af7_body_gold_damage.rvmat"}},
						{0.3, {"AF_Weapons\af7_vanguard\data\af7_body_gold_damage.rvmat"}},
						{0.0, {"AF_Weapons\af7_vanguard\data\af7_body_gold_destruct.rvmat"}}
					};
				};
			};
		};
	};

	// AF M41 "Pathfinder": WW2-style bolt-action sniper rifle.
	// Inherits the vanilla Mosin 91/30: its animations, sounds, recoil, 5-round internal
	// magazine, 7.62x54R ammunition and stripper clip. The model is built in the Mosin's
	// own frame with the Mosin's bone names, so only the model and textures are ours.
	class AFM41_Pathfinder: Mosin9130
	{
		scope = 2;
		displayName = "AF M41 Pathfinder";
		descriptionShort = "An Allied Forces bolt-action sniper rifle in the pattern of the early 1940s: a long walnut stock, a turned-down bolt and a five-round internal magazine. It fires 7.62x54mmR, loads from stripper clips and takes the PU scope.";
		weight = 4000;
		model = "\AF_Weapons\afm41_pathfinder\afm41_pathfinder.p3d";

		// A touch steadier and more accurate than the service rifle it is based on.
		swayModifier[] = {2.2, 2.2, 0.9};

		// Slots the model has proxies for: ghillie wrap, PU scope, Mosin compensator,
		// improvised suppressor, Mosin bayonet. Same list as the vanilla Mosin.
		attachments[] = {"weaponWrap", "weaponOpticsMosin", "weaponMuzzleMosin", "suppressorImpro", "weaponBayonetMosin"};
		hiddenSelections[] = {"camo", "hide_barrel"};
		hiddenSelectionsTextures[] = {"AF_Weapons\afm41_pathfinder\data\afm41_body_co.paa", "AF_Weapons\afm41_pathfinder\data\afm41_body_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afm41_pathfinder\data\afm41_body.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_body.rvmat"};

		// Iron sights: no depth-of-field blur when aiming (same choice as the AF-7).
		// The other values are the Mosin's.
		PPDOFProperties[] = {0, 0.5, 20, 170, 4, 10};

		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 250;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afm41_pathfinder\data\afm41_body.rvmat"}},
						{0.7, {"AF_Weapons\afm41_pathfinder\data\afm41_body.rvmat"}},
						{0.5, {"AF_Weapons\afm41_pathfinder\data\afm41_body_damage.rvmat"}},
						{0.3, {"AF_Weapons\afm41_pathfinder\data\afm41_body_damage.rvmat"}},
						{0.0, {"AF_Weapons\afm41_pathfinder\data\afm41_body_destruct.rvmat"}}
					};
				};
			};
		};
	};

	// Gold floral finish: black furniture with the gold floral pattern of the AF-7 Gold,
	// blued steel unchanged. Not in the loot tables by default.
	class AFM41_Pathfinder_Gold: AFM41_Pathfinder
	{
		scope = 2;
		displayName = "AF M41 Pathfinder (Gold)";
		descriptionShort = "An Allied Forces M41 Pathfinder with gold floral furniture on black. It fires 7.62x54mmR, loads from stripper clips and takes the PU scope.";
		hiddenSelectionsTextures[] = {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold_co.paa", "AF_Weapons\afm41_pathfinder\data\afm41_body_gold_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_body_gold.rvmat"};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 250;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold.rvmat"}},
						{0.7, {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold.rvmat"}},
						{0.5, {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold_damage.rvmat"}},
						{0.3, {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold_damage.rvmat"}},
						{0.0, {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold_destruct.rvmat"}}
					};
				};
			};
		};
	};
};