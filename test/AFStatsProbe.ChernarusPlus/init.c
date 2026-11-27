// Stats probe for the Allied Forces Weapons Pack. Offline, DayZDiag only.
//
// Prints the stats of every AF weapon as the running game resolves them, inherited values included
// (the public script API, GetGame().ConfigGet...; nothing is read from game files): weight, inventory
// size, fire modes with their cycle time, burst size and dispersion, recoil and sway modifiers, each
// magazine with its capacity, and each round it fires with its speed and damage. For the Workshop
// cards (workshop/cards.json), where our own config leaves a value to the vanilla base class.
// Start it with: test\run_test.ps1 -Mission AFStatsProbe.ChernarusPlus -TimeoutSeconds 120
// The lines are in test\profiles\script_*.log, each starting with [AFStats].

string AFS_Array(string path)
{
	TStringArray a = new TStringArray;
	GetGame().ConfigGetTextArray(path, a);
	string s = "";
	foreach (string v : a)
	{
		if (s != "")
			s = s + ",";
		s = s + v;
	}
	return s;
}

string AFS_Floats(string path)
{
	TFloatArray a = new TFloatArray;
	GetGame().ConfigGetFloatArray(path, a);
	string s = "";
	foreach (float v : a)
	{
		if (s != "")
			s = s + ",";
		s = s + v.ToString();
	}
	return s;
}

void AFS_Bullet(string weapon, string pile)
{
	string bullet;
	GetGame().ConfigGetText("CfgMagazines " + pile + " ammo", bullet);
	if (bullet == "")
		return;
	string b = "CfgAmmo " + bullet;
	string line = "[AFStats] " + weapon + " round " + pile + " bullet " + bullet;
	line = line + " initSpeed " + GetGame().ConfigGetFloat(b + " initSpeed").ToString();
	line = line + " hit " + GetGame().ConfigGetFloat(b + " hit").ToString();
	line = line + " health " + GetGame().ConfigGetFloat(b + " DamageApplied Health damage").ToString();
	line = line + " blood " + GetGame().ConfigGetFloat(b + " DamageApplied Blood damage").ToString();
	line = line + " shock " + GetGame().ConfigGetFloat(b + " DamageApplied Shock damage").ToString();
	Print(line);
}

void AFS_Weapon(string cls)
{
	string w = "CfgWeapons " + cls;
	string name;
	GetGame().ConfigGetText(w + " displayName", name);
	Print("[AFStats] " + cls + " name " + name);
	Print("[AFStats] " + cls + " weight_g " + GetGame().ConfigGetFloat(w + " weight").ToString() + " itemSize " + AFS_Floats(w + " itemSize"));
	Print("[AFStats] " + cls + " recoilModifier " + AFS_Floats(w + " recoilModifier") + " swayModifier " + AFS_Floats(w + " swayModifier"));
	Print("[AFStats] " + cls + " attachments " + AFS_Array(w + " attachments"));
	Print("[AFStats] " + cls + " zeroing " + AFS_Floats(w + " OpticsInfo discreteDistance"));

	TStringArray modes = new TStringArray;
	GetGame().ConfigGetTextArray(w + " modes", modes);
	foreach (string m : modes)
	{
		string p = w + " " + m;
		string line = "[AFStats] " + cls + " mode " + m;
		line = line + " reloadTime " + GetGame().ConfigGetFloat(p + " reloadTime").ToString();
		line = line + " burst " + GetGame().ConfigGetInt(p + " burst").ToString();
		line = line + " autoFire " + GetGame().ConfigGetInt(p + " autoFire").ToString();
		line = line + " dispersion " + GetGame().ConfigGetFloat(p + " dispersion").ToString();
		Print(line);
	}

	TStringArray mags = new TStringArray;
	GetGame().ConfigGetTextArray(w + " magazines", mags);
	foreach (string mag : mags)
	{
		string pile;
		GetGame().ConfigGetText("CfgMagazines " + mag + " ammo", pile);
		Print("[AFStats] " + cls + " magazine " + mag + " count " + GetGame().ConfigGetInt("CfgMagazines " + mag + " count").ToString() + " weight_g " + GetGame().ConfigGetFloat("CfgMagazines " + mag + " weight").ToString() + " ammoItems " + AFS_Array("CfgMagazines " + mag + " ammoItems"));
	}
	Print("[AFStats] " + cls + " internal chamberSize " + GetGame().ConfigGetInt(w + " chamberSize").ToString() + " internalMagazine " + AFS_Array(w + " chamberableFrom"));

	TStringArray piles = new TStringArray;
	GetGame().ConfigGetTextArray(w + " chamberableFrom", piles);
	foreach (string pl : piles)
		AFS_Bullet(cls, pl);
}

void main()
{
	TStringArray all = {"AF7_Vanguard", "AFM41_Pathfinder", "AF_MP40", "AF_P08", "AF_StG44", "AF_M107A1", "AF_PeaceKeeper"};
	foreach (string cls : all)
		AFS_Weapon(cls);
	// The scopes of our own that zero: their ranges.
	TStringArray optics = {"AF_ZF4Optic", "AF_M107Scope"};
	foreach (string o : optics)
		Print("[AFStats] " + o + " zeroing " + AFS_Floats("CfgVehicles " + o + " OpticsInfo discreteDistance"));
	Print("[AFStats] DONE");
}

class CustomMission: MissionGameplay
{
	override void OnInit()
	{
		super.OnInit();
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFQuit, 8000, false);
	}

	void AFQuit()
	{
		GetGame().RequestExit(0);
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
