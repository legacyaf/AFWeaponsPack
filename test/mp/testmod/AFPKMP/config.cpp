// Test-only helper for test\mp\run_mp.ps1. Never ship this.
// On the client it raises the PeaceKeeper, asks the test script to hold the trigger in each fire mode,
// and logs the rounds fired and the round counter. On the server it keeps the rifle on this
// unlicensed local test server (the real licence answer is still logged).
class CfgPatches
{
	class AFPKMP
	{
		units[] = {};
		weapons[] = {};
		requiredVersion = 0.1;
		requiredAddons[] = {"AF_Weapons"};
	};
};

class CfgMods
{
	class AFPKMP
	{
		dir = "AFPKMP";
		name = "AF Weapons multiplayer test helper";
		type = "mod";
		dependencies[] = {"World", "Mission"};
		class defs
		{
			class worldScriptModule
			{
				value = "";
				files[] = {"AFPKMP/Scripts/4_World"};
			};
			class missionScriptModule
			{
				value = "";
				files[] = {"AFPKMP/Scripts/5_Mission"};
			};
		};
	};
};
