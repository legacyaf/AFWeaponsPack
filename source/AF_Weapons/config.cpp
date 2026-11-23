////////////////////////////////////////////////////////////////////
// Allied Forces Weapons Pack
//
// AF-7 "Vanguard"    - original Allied Forces assault rifle, 5.56x45 / .308.
// AF M41 "Pathfinder" - WW2-style bolt-action sniper rifle, 7.62x54R (inherits the Mosin 91/30).
// AF MP40           - WW2-style 9 mm submachine gun with its own 32-round magazine (inherits the UMP-45).
// AF P08            - toggle-lock 9 mm pistol with its own 8-round magazine (inherits the P1).
// AF StG 44         - WW2-style assault rifle with its own curved magazine and ZF4 scope (inherits the AKM).
//
// Each weapon inherits a vanilla weapon (M4A1, Mosin 91/30, UMP-45, P1). That gives it that
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
		units[] = {"AF_WeaponRepairKit", "AF_ZF4Optic"};
		weapons[] = {"AF7_Vanguard", "AF7_Vanguard_Gold", "AFM41_Pathfinder", "AFM41_Pathfinder_Gold", "AF_MP40", "AF_MP40_Gold", "AF_P08", "AF_P08_Gold", "AF_StG44", "AF_StG44_Gold"};
		requiredVersion = 0.1;
		requiredAddons[] = {"DZ_Data", "DZ_Scripts", "DZ_Weapons_Firearms", "DZ_Weapons_Firearms_M4", "DZ_Weapons_Firearms_FAL", "DZ_Weapons_Firearms_MosinNagant", "DZ_Weapons_Firearms_UMP", "DZ_Weapons_Firearms_MP5", "DZ_Weapons_Magazines", "DZ_Pistols", "DZ_Pistols_p1", "DZ_Gear_Tools", "DZ_Weapons_Firearms_AKM", "DZ_Weapons_Optics"};
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
		version = "0.12.0";
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

class Mode_FullAuto;

class CfgWeapons
{
	class M4A1;
	class Mosin9130;
	class UMP45;
	class P1;
	class AKM_Base;
	class AKM: AKM_Base
	{
		class FullAuto;
	};

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
		hiddenSelections[] = {"camo", "hide_barrel", "camo1"};   // [MODEL] the muzzle brake is retextured with the body
		hiddenSelectionsTextures[] = {"AF_Weapons\af7_vanguard\data\af7_body_co.paa", "AF_Weapons\af7_vanguard\data\af7_body_co.paa", "AF_Weapons\af7_vanguard\data\af7_furn_co.paa"};   // [MODEL]
		hiddenSelectionsMaterials[] = {"AF_Weapons\af7_vanguard\data\af7_body.rvmat", "AF_Weapons\af7_vanguard\data\af7_body.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn.rvmat"};   // [MODEL]

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
						{1.0, {"AF_Weapons\af7_vanguard\data\af7_body.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn.rvmat"}},            // [MODEL]
						{0.7, {"AF_Weapons\af7_vanguard\data\af7_body.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn.rvmat"}},            // [MODEL]
						{0.5, {"AF_Weapons\af7_vanguard\data\af7_body_damage.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn_damage.rvmat"}},     // [MODEL]
						{0.3, {"AF_Weapons\af7_vanguard\data\af7_body_damage.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn_damage.rvmat"}},     // [MODEL]
						{0.0, {"AF_Weapons\af7_vanguard\data\af7_body_destruct.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn_destruct.rvmat"}}    // [MODEL]
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
		hiddenSelectionsTextures[] = {"AF_Weapons\af7_vanguard\data\af7_body_gold_co.paa", "AF_Weapons\af7_vanguard\data\af7_body_gold_co.paa", "AF_Weapons\af7_vanguard\data\af7_furn_gold_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\af7_vanguard\data\af7_body_gold.rvmat", "AF_Weapons\af7_vanguard\data\af7_body_gold.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn_gold.rvmat"};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 200;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\af7_vanguard\data\af7_body_gold.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn_gold.rvmat"}},
						{0.7, {"AF_Weapons\af7_vanguard\data\af7_body_gold.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn_gold.rvmat"}},
						{0.5, {"AF_Weapons\af7_vanguard\data\af7_body_gold_damage.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn_gold_damage.rvmat"}},
						{0.3, {"AF_Weapons\af7_vanguard\data\af7_body_gold_damage.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn_gold_damage.rvmat"}},
						{0.0, {"AF_Weapons\af7_vanguard\data\af7_body_gold_destruct.rvmat", "AF_Weapons\af7_vanguard\data\af7_furn_gold_destruct.rvmat"}}
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
		hiddenSelections[] = {"camo", "hide_barrel", "camo1"};
		hiddenSelectionsTextures[] = {"AF_Weapons\afm41_pathfinder\data\afm41_body_co.paa", "AF_Weapons\afm41_pathfinder\data\afm41_body_co.paa", "AF_Weapons\afm41_pathfinder\data\afm41_wood_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afm41_pathfinder\data\afm41_body.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_body.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood.rvmat"};

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
						{1.0, {"AF_Weapons\afm41_pathfinder\data\afm41_body.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood.rvmat"}},
						{0.7, {"AF_Weapons\afm41_pathfinder\data\afm41_body.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood.rvmat"}},
						{0.5, {"AF_Weapons\afm41_pathfinder\data\afm41_body_damage.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood_damage.rvmat"}},
						{0.3, {"AF_Weapons\afm41_pathfinder\data\afm41_body_damage.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood_damage.rvmat"}},
						{0.0, {"AF_Weapons\afm41_pathfinder\data\afm41_body_destruct.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood_destruct.rvmat"}}
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
		hiddenSelectionsTextures[] = {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold_co.paa", "AF_Weapons\afm41_pathfinder\data\afm41_body_gold_co.paa", "AF_Weapons\afm41_pathfinder\data\afm41_wood_gold_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_body_gold.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood_gold.rvmat"};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 250;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood_gold.rvmat"}},
						{0.7, {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood_gold.rvmat"}},
						{0.5, {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold_damage.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood_gold_damage.rvmat"}},
						{0.3, {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold_damage.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood_gold_damage.rvmat"}},
						{0.0, {"AF_Weapons\afm41_pathfinder\data\afm41_body_gold_destruct.rvmat", "AF_Weapons\afm41_pathfinder\data\afm41_wood_gold_destruct.rvmat"}}
					};
				};
			};
		};
	};

	// AF MP40: WW2-style 9 mm submachine gun.
	// Inherits the vanilla UMP-45: its animations, handling and recoil. The model is built in the
	// UMP's own frame with the UMP's bone names. Different from the UMP: 9x19 ammunition, its own
	// 32-round magazine (CfgMagazines below), automatic fire only at about 520 rounds a minute,
	// and the 9 mm sounds of the MP5-K.
	class AF_MP40: UMP45
	{
		scope = 2;
		displayName = "AF MP40";
		descriptionShort = "An Allied Forces submachine gun in the pattern of the early 1940s: a steel tube receiver, bakelite furniture and an under-folding stock. It fires 9x19mm from its own 32-round stick magazine, automatic only, at a slow and steady rate.";
		weight = 4000;
		model = "\AF_Weapons\afmp40\afmp40.p3d";
		itemSize[] = {6, 3};

		chamberableFrom[] = {"Ammo_9x19"};
		magazines[] = {"Mag_AFMP40_32Rnd"};

		// The barrel is 13 cm longer than the UMP's, measured from the same origin.
		WeaponLength = 0.794;
		ObstructionDistance = 0.594;

		// Slots the model has proxies for: ghillie wrap and pistol suppressor.
		attachments[] = {"weaponWrap", "pistolMuzzle"};
		hiddenSelections[] = {"camo", "hide_barrel", "camo1"};
		hiddenSelectionsTextures[] = {"AF_Weapons\afmp40\data\afmp40_body_co.paa", "AF_Weapons\afmp40\data\afmp40_body_co.paa", "AF_Weapons\afmp40\data\afmp40_furn_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afmp40\data\afmp40_body.rvmat", "AF_Weapons\afmp40\data\afmp40_body.rvmat", "AF_Weapons\afmp40\data\afmp40_furn.rvmat"};

		// Iron sights: no depth-of-field blur when aiming (same choice as the other AF weapons).
		PPDOFProperties[] = {0, 0.75, 20, 170, 4, 10};

		// Heavy for its calibre and slow firing, so it is easy to hold on target.
		recoilModifier[] = {0.85, 0.85, 0.85};

		modes[] = {"FullAuto"};
		class FullAuto: Mode_FullAuto
		{
			soundSetShot1st[] = {"MP5K_Shot_1st_SoundSet", "MP5K_Shot_1st_iterior_SoundSet"};
			soundSetShot[] = {"MP5K_Shot_SoundSet", "MP5K_Shot_iterior_SoundSet", "MP5K_Tail_SoundSet", "MP5K_InteriorTail_SoundSet", "MP5K_Slapback_SoundSet", "MP5K_Tail_2D_SoundSet"};
			soundSetShotExt1st[] = {{"MP5K_1st_silencer_SoundSet"}, {"MP5K_1st_silencerHomeMade_SoundSet"}};
			soundSetShotExt[] =
			{
				{"MP5K_silencer_SoundSet", "MP5K_silencerTail_SoundSet", "MP5K_silencerInteriorTail_SoundSet"},
				{"MP5K_silencerHomeMade_SoundSet", "MP5K_silencerHomeMadeTail_SoundSet", "MP5K_silencerInteriorHomeMadeTail_SoundSet"}
			};
			reloadTime = 0.115;
			recoil = "recoil_auto_primary_7outof10";
			recoilProne = "recoil_auto_primary_prone_7outof10";
			dispersion = 0.003;
			magazineSlot = "magazine";
		};

		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 250;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afmp40\data\afmp40_body.rvmat", "AF_Weapons\afmp40\data\afmp40_furn.rvmat"}},
						{0.7, {"AF_Weapons\afmp40\data\afmp40_body.rvmat", "AF_Weapons\afmp40\data\afmp40_furn.rvmat"}},
						{0.5, {"AF_Weapons\afmp40\data\afmp40_body_damage.rvmat", "AF_Weapons\afmp40\data\afmp40_furn_damage.rvmat"}},
						{0.3, {"AF_Weapons\afmp40\data\afmp40_body_damage.rvmat", "AF_Weapons\afmp40\data\afmp40_furn_damage.rvmat"}},
						{0.0, {"AF_Weapons\afmp40\data\afmp40_body_destruct.rvmat", "AF_Weapons\afmp40\data\afmp40_furn_destruct.rvmat"}}
					};
				};
			};
		};
	};

	// Gold floral finish: black furniture with the gold floral pattern, steel unchanged.
	// Not in the loot tables by default.
	class AF_MP40_Gold: AF_MP40
	{
		scope = 2;
		displayName = "AF MP40 (Gold)";
		descriptionShort = "An Allied Forces MP40 with gold floral furniture on black. It fires 9x19mm from its own 32-round stick magazine, automatic only.";
		hiddenSelectionsTextures[] = {"AF_Weapons\afmp40\data\afmp40_body_gold_co.paa", "AF_Weapons\afmp40\data\afmp40_body_gold_co.paa", "AF_Weapons\afmp40\data\afmp40_furn_gold_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afmp40\data\afmp40_body_gold.rvmat", "AF_Weapons\afmp40\data\afmp40_body_gold.rvmat", "AF_Weapons\afmp40\data\afmp40_furn_gold.rvmat"};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 250;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afmp40\data\afmp40_body_gold.rvmat", "AF_Weapons\afmp40\data\afmp40_furn_gold.rvmat"}},
						{0.7, {"AF_Weapons\afmp40\data\afmp40_body_gold.rvmat", "AF_Weapons\afmp40\data\afmp40_furn_gold.rvmat"}},
						{0.5, {"AF_Weapons\afmp40\data\afmp40_body_gold_damage.rvmat", "AF_Weapons\afmp40\data\afmp40_furn_gold_damage.rvmat"}},
						{0.3, {"AF_Weapons\afmp40\data\afmp40_body_gold_damage.rvmat", "AF_Weapons\afmp40\data\afmp40_furn_gold_damage.rvmat"}},
						{0.0, {"AF_Weapons\afmp40\data\afmp40_body_gold_destruct.rvmat", "AF_Weapons\afmp40\data\afmp40_furn_gold_destruct.rvmat"}}
					};
				};
			};
		};
	};

	// AF P08: toggle-lock 9 mm service pistol.
	// Inherits the vanilla P1: its animations, sounds, recoil and handling. The model is built in the
	// P1's own frame with the P1's bone names. Different from the P1: its own 8-round magazine
	// (CfgMagazines below) and a slot for the pistol suppressor as well as the improvised one.
	class AF_P08: P1
	{
		scope = 2;
		displayName = "AF P08";
		descriptionShort = "An Allied Forces service pistol in the pattern of 1908: a toggle-locked action, a slim tapered barrel and a steeply raked grip with checkered walnut panels. It fires 9x19mm from its own 8-round magazine.";
		weight = 870;
		model = "\AF_Weapons\afp08\afp08.p3d";

		magazines[] = {"Mag_AFP08_8Rnd"};

		// Slots the model has proxies for: improvised suppressor and pistol suppressor.
		attachments[] = {"suppressorImpro", "pistolMuzzle"};
		hiddenSelections[] = {"camo"};
		hiddenSelectionsTextures[] = {"AF_Weapons\afp08\data\afp08_body_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afp08\data\afp08_body.rvmat"};

		// Iron sights: no depth-of-field blur when aiming (same choice as the other AF weapons).
		// The other values are the P1's.
		PPDOFProperties[] = {0, 0.55, 10, 240, 4, 10};

		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 200;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afp08\data\afp08_body.rvmat"}},
						{0.7, {"AF_Weapons\afp08\data\afp08_body.rvmat"}},
						{0.5, {"AF_Weapons\afp08\data\afp08_body_damage.rvmat"}},
						{0.3, {"AF_Weapons\afp08\data\afp08_body_damage.rvmat"}},
						{0.0, {"AF_Weapons\afp08\data\afp08_body_destruct.rvmat"}}
					};
				};
			};
		};
	};

	// Gold floral finish: black grips with the gold floral pattern, blued steel unchanged.
	// Not in the loot tables by default.
	class AF_P08_Gold: AF_P08
	{
		scope = 2;
		displayName = "AF P08 (Gold)";
		descriptionShort = "An Allied Forces P08 with gold floral grips on black. It fires 9x19mm from its own 8-round magazine.";
		hiddenSelectionsTextures[] = {"AF_Weapons\afp08\data\afp08_body_gold_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afp08\data\afp08_body_gold.rvmat"};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 200;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afp08\data\afp08_body_gold.rvmat"}},
						{0.7, {"AF_Weapons\afp08\data\afp08_body_gold.rvmat"}},
						{0.5, {"AF_Weapons\afp08\data\afp08_body_gold_damage.rvmat"}},
						{0.3, {"AF_Weapons\afp08\data\afp08_body_gold_damage.rvmat"}},
						{0.0, {"AF_Weapons\afp08\data\afp08_body_gold_destruct.rvmat"}}
					};
				};
			};
		};
	};

	// AF StG 44: WW2-style assault rifle.
	// Inherits the vanilla AKM: its animations, handling, recoil and sounds. The model is built in the
	// AKM's own frame with the AKM's bone names. Different from the AKM: its own curved 30-round
	// magazine (CfgMagazines below), its own ZF4-style scope (CfgVehicles below, slot
	// weaponOpticsAFStG), a slower rate of fire and no stock, handguard or bayonet slots.
	// Because of the AKM animations the cocking handle is on the right and it fires 7.62x39.
	// From this weapon on: no AF logo, "legacy was here" scratched on the right of the receiver.
	class AF_StG44: AKM
	{
		scope = 2;
		displayName = "AF StG 44";
		descriptionShort = "An Allied Forces assault rifle in the pattern of 1944: a stamped steel receiver, a beech stock and a long curved 30-round magazine. It fires 7.62x39mm, single shots or automatic at a steady rate. It takes its own ZF4 scope.";
		weight = 4600;
		model = "\AF_Weapons\afstg44\afstg44.p3d";
		itemSize[] = {8, 3};

		magazines[] = {"Mag_AFStG44_30Rnd"};

		// The muzzle is 3.7 cm further forward than the AKM's, measured from the same origin.
		WeaponLength = 0.937;
		ObstructionDistance = 0.649;

		// Slots the model has proxies for: ghillie wrap, its own scope, the AK suppressor and the
		// improvised suppressor.
		attachments[] = {"weaponWrap", "weaponOpticsAFStG", "weaponMuzzleAK", "suppressorImpro"};
		hiddenSelections[] = {"camo", "hide_barrel", "camo1"};
		hiddenSelectionsTextures[] = {"AF_Weapons\afstg44\data\afstg44_body_co.paa", "AF_Weapons\afstg44\data\afstg44_body_co.paa", "AF_Weapons\afstg44\data\afstg44_wood_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afstg44\data\afstg44_body.rvmat", "AF_Weapons\afstg44\data\afstg44_body.rvmat", "AF_Weapons\afstg44\data\afstg44_wood.rvmat"};

		// Iron sights: no depth-of-field blur when aiming (same choice as the other AF weapons).
		PPDOFProperties[] = {0, 0.5, 50, 160, 4, 10};

		// Heavier than the AKM, so it climbs a little less.
		recoilModifier[] = {0.9, 0.9, 0.9};

		class FullAuto: FullAuto
		{
			reloadTime = 0.105;      // about 570 rounds a minute (AKM: 0.098, about 610)
		};

		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 300;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afstg44\data\afstg44_body.rvmat", "AF_Weapons\afstg44\data\afstg44_wood.rvmat"}},
						{0.7, {"AF_Weapons\afstg44\data\afstg44_body.rvmat", "AF_Weapons\afstg44\data\afstg44_wood.rvmat"}},
						{0.5, {"AF_Weapons\afstg44\data\afstg44_body_damage.rvmat", "AF_Weapons\afstg44\data\afstg44_wood_damage.rvmat"}},
						{0.3, {"AF_Weapons\afstg44\data\afstg44_body_damage.rvmat", "AF_Weapons\afstg44\data\afstg44_wood_damage.rvmat"}},
						{0.0, {"AF_Weapons\afstg44\data\afstg44_body_destruct.rvmat", "AF_Weapons\afstg44\data\afstg44_wood_destruct.rvmat"}}
					};
				};
			};
		};
	};

	// Gold floral finish: black stock and grips with the gold floral pattern, steel unchanged.
	// Not in the loot tables by default.
	class AF_StG44_Gold: AF_StG44
	{
		scope = 2;
		displayName = "AF StG 44 (Gold)";
		descriptionShort = "An Allied Forces StG 44 with gold floral furniture on black. It fires 7.62x39mm from its own curved 30-round magazine.";
		hiddenSelectionsTextures[] = {"AF_Weapons\afstg44\data\afstg44_body_gold_co.paa", "AF_Weapons\afstg44\data\afstg44_body_gold_co.paa", "AF_Weapons\afstg44\data\afstg44_wood_gold_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afstg44\data\afstg44_body_gold.rvmat", "AF_Weapons\afstg44\data\afstg44_body_gold.rvmat", "AF_Weapons\afstg44\data\afstg44_wood_gold.rvmat"};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 300;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afstg44\data\afstg44_body_gold.rvmat", "AF_Weapons\afstg44\data\afstg44_wood_gold.rvmat"}},
						{0.7, {"AF_Weapons\afstg44\data\afstg44_body_gold.rvmat", "AF_Weapons\afstg44\data\afstg44_wood_gold.rvmat"}},
						{0.5, {"AF_Weapons\afstg44\data\afstg44_body_gold_damage.rvmat", "AF_Weapons\afstg44\data\afstg44_wood_gold_damage.rvmat"}},
						{0.3, {"AF_Weapons\afstg44\data\afstg44_body_gold_damage.rvmat", "AF_Weapons\afstg44\data\afstg44_wood_gold_damage.rvmat"}},
						{0.0, {"AF_Weapons\afstg44\data\afstg44_body_gold_destruct.rvmat", "AF_Weapons\afstg44\data\afstg44_wood_gold_destruct.rvmat"}}
					};
				};
			};
		};
	};
};

// Weapon repair kit. It looks like the game's weapon cleaning kit and is used the same way (combine it
// with the weapon), but only repairs weapons of this pack, and can bring a ruined one back. Time, amount
// restored, uses per kit and whether it works on suppressors are server settings (AF_WeaponsPack.json).
class CfgVehicles
{
	class WeaponCleaningKit;
	class AF_WeaponRepairKit: WeaponCleaningKit
	{
		scope = 2;
		displayName = "AF Weapon Repair Kit";
		descriptionShort = "An armourer's kit for Allied Forces weapons. Combine it with a weapon of the pack to repair it, even a ruined one. It does nothing for other weapons.";
		repairKitType = 99;      // no item lists kit type 99, so the game's own cleaning recipe ignores this kit
	};

	// The AF StG 44's own scope, in the style of the 4x ZF4. It inherits the vanilla PU scope (its
	// handling and the way the view works) and fits only the StG 44 (slot weaponOpticsAFStG).
	class PUScopeOptic;
	class AF_ZF4Optic: PUScopeOptic
	{
		scope = 2;
		displayName = "AF ZF4 Scope";
		descriptionShort = "A 4x telescopic sight on a side clamp mount, made for the AF StG 44. It fits no other weapon.";
		model = "\AF_Weapons\afstg44\afzf4.p3d";
		weight = 600;
		itemSize[] = {3, 1};
		inventorySlot[] = {"weaponOpticsAFStG"};
		hiddenSelections[] = {"camo"};
		hiddenSelectionsTextures[] = {"AF_Weapons\afstg44\data\afzf4_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afstg44\data\afzf4.rvmat"};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 50;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afstg44\data\afzf4.rvmat"}},
						{0.7, {"AF_Weapons\afstg44\data\afzf4.rvmat"}},
						{0.5, {"AF_Weapons\afstg44\data\afzf4_damage.rvmat"}},
						{0.3, {"AF_Weapons\afstg44\data\afzf4_damage.rvmat"}},
						{0.0, {"AF_Weapons\afstg44\data\afzf4_destruct.rvmat"}}
					};
				};
			};
		};
		class OpticsInfo
		{
			memoryPointCamera = "eyeScope";
			cameraDir = "cameraDir";
			modelOptics = "-";
			opticsDisablePeripherialVision = 0.67;
			opticsFlare = 1;
			// Owner's test (2026-11-23): too zoomed in and not clear. 3x instead of 4x, and only a light
			// colour fringe: no blur effect over the picture (it was the strongest chromatic aberration
			// plus a blur pass).
			opticsPPEffects[] = {"OpticsCHAbera1"};
			opticsZoomMin = "0.3926/3";
			opticsZoomMax = "0.3926/3";
			opticsZoomInit = "0.3926/3";
			distanceZoomMin = 100;
			distanceZoomMax = 800;
			discreteDistance[] = {100, 200, 300, 400, 500, 600, 700, 800};
			discreteDistanceInitIndex = 0;
			PPMaskProperties[] = {0.5, 0.5, 0.35, 0.05};
			PPLensProperties[] = {0.5, 0.15, 0, 0};
			PPBlurProperties = 0.2;
		};
	};
};

// The AF MP40's own magazine. It inherits the UMP-45 magazine (same slot, same handling and
// sounds) and changes the model, the capacity and the ammunition.
class CfgMagazines
{
	class Mag_UMP_25Rnd;
	class Mag_AFMP40_32Rnd: Mag_UMP_25Rnd
	{
		scope = 2;
		displayName = "AF MP40 32rd Magazine";
		descriptionShort = "A 32-round steel stick magazine for the AF MP40. It holds 9x19mm rounds.";
		model = "\AF_Weapons\afmp40\afmp40_mag.p3d";
		weight = 250;
		weightPerQuantityUnit = 8;
		itemSize[] = {1, 3};
		count = 32;
		ammo = "Bullet_9x19";
		ammoItems[] = {"Ammo_9x19"};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 100;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afmp40\data\afmp40_mag.rvmat"}},
						{0.7, {"AF_Weapons\afmp40\data\afmp40_mag.rvmat"}},
						{0.5, {"AF_Weapons\afmp40\data\afmp40_mag_damage.rvmat"}},
						{0.3, {"AF_Weapons\afmp40\data\afmp40_mag_damage.rvmat"}},
						{0.0, {"AF_Weapons\afmp40\data\afmp40_mag_destruct.rvmat"}}
					};
				};
			};
		};
	};

	// The AF P08's own magazine. It inherits the P1 magazine (same slot, handling and sounds)
	// and changes the model.
	class Mag_P1_8Rnd;
	class Mag_AFP08_8Rnd: Mag_P1_8Rnd
	{
		scope = 2;
		displayName = "AF P08 8rd Magazine";
		descriptionShort = "An 8-round magazine for the AF P08, with a wooden base. It holds 9x19mm rounds.";
		model = "\AF_Weapons\afp08\afp08_mag.p3d";
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 100;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afp08\data\afp08_mag.rvmat"}},
						{0.7, {"AF_Weapons\afp08\data\afp08_mag.rvmat"}},
						{0.5, {"AF_Weapons\afp08\data\afp08_mag_damage.rvmat"}},
						{0.3, {"AF_Weapons\afp08\data\afp08_mag_damage.rvmat"}},
						{0.0, {"AF_Weapons\afp08\data\afp08_mag_destruct.rvmat"}}
					};
				};
			};
		};
	};

	// The AF StG 44's own magazine. It inherits the AKM magazine (same slot, handling, sounds and
	// ammunition) and changes the model.
	class Mag_AKM_30Rnd;
	class Mag_AFStG44_30Rnd: Mag_AKM_30Rnd
	{
		scope = 2;
		displayName = "AF StG 44 30rd Magazine";
		descriptionShort = "A long, curved 30-round steel magazine for the AF StG 44. It holds 7.62x39mm rounds.";
		model = "\AF_Weapons\afstg44\afstg44_mag.p3d";
		weight = 400;
		itemSize[] = {1, 3};
		// The AKM magazine swaps its own texture onto "camo" (seen as stripes in the first in-game
		// test); this one has its own.
		hiddenSelections[] = {"camo"};
		hiddenSelectionsTextures[] = {"AF_Weapons\afstg44\data\afstg44_mag_co.paa"};
		hiddenSelectionsMaterials[] = {"AF_Weapons\afstg44\data\afstg44_mag.rvmat"};
		class DamageSystem
		{
			class GlobalHealth
			{
				class Health
				{
					hitpoints = 100;
					healthLevels[] =
					{
						{1.0, {"AF_Weapons\afstg44\data\afstg44_mag.rvmat"}},
						{0.7, {"AF_Weapons\afstg44\data\afstg44_mag.rvmat"}},
						{0.5, {"AF_Weapons\afstg44\data\afstg44_mag_damage.rvmat"}},
						{0.3, {"AF_Weapons\afstg44\data\afstg44_mag_damage.rvmat"}},
						{0.0, {"AF_Weapons\afstg44\data\afstg44_mag_destruct.rvmat"}}
					};
				};
			};
		};
	};
};

// The scope slot only the AF StG 44 has, so its scope fits nothing else and other scopes do not fit it.
class CfgSlots
{
	class Slot_weaponOpticsAFStG
	{
		name = "weaponOpticsAFStG";
		displayName = "Optics";
		ghostIcon = "set:dayz_inventory image:weaponoptics";
	};
};

// Tells the game which slot the scope proxy in afstg44.p3d belongs to. Without it the scope model
// is drawn on every StG 44, attached or not (seen in the first in-game test).
class CfgNonAIVehicles
{
	class ProxyAttachment;
	class Proxyafzf4: ProxyAttachment
	{
		scope = 2;
		inventorySlot = "weaponOpticsAFStG";
		model = "\AF_Weapons\afstg44\afzf4.p3d";
	};
};
