////////////////////////////////////////////////////////////////////
// Allied Forces Flags
//
// Custom flags for the territory flagpole. Each one inherits the
// vanilla Flag_Base, so it uses the vanilla flag model and behaves
// like any other flag: only the texture is ours.
//
// The texture is the whole flag, 2:1 (1024 x 512), upright, read
// left to right - the same layout as the vanilla flag textures.
////////////////////////////////////////////////////////////////////

class CfgPatches
{
	class AF_Flags
	{
		units[] = {"Flag_AF_Sierra"};
		weapons[] = {};
		requiredVersion = 0.1;
		requiredAddons[] = {"DZ_Data", "DZ_Gear_Camping"};
	};
};

class CfgVehicles
{
	class Flag_Base;

	class Flag_AF_Sierra: Flag_Base
	{
		scope = 2;
		displayName = "Allied Forces Flag (Sierra)";
		descriptionShort = "An Allied Forces flag: a white Sierra parked in front of an A-10. Raise it on a flagpole to claim a base.";
		hiddenSelectionsTextures[] = {"AF_Flags\data\flag_af_sierra_co.paa"};
		color = "AFSierra";
	};
};
