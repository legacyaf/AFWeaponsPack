// Probe mission: reads the vanilla SCAR-H's frame from the running game, for The PeaceKeeper (which
// inherits it). Uses only the public script API; nothing is extracted from the game files. Logs:
//   - the SCAR class names in CfgWeapons and CfgMagazines (to find the rifle and its magazines);
//   - the rifle's memory points, attachment slots and where its magazine sits;
//   - where the player's hands hold it, at rest and raised (aimed);
//   - its fire modes (config) and collision box.
// Then quits. Start it with: test\run_test.ps1 -Mission AFScarProbe.ChernarusPlus

PlayerBase g_P;
Weapon_Base g_W;
string g_Rifle;
string g_Mag;

string V(vector v)
{
	return string.Format("%1 %2 %3", v[0].ToString(), v[1].ToString(), v[2].ToString());
}

void ListClasses(string root, out TStringArray found)
{
	int n = GetGame().ConfigGetChildrenCount(root);
	for (int i = 0; i < n; i++)
	{
		string c;
		GetGame().ConfigGetChildName(root, i, c);
		string lc = c;
		lc.ToLower();
		if (lc.Contains("scar"))
		{
			found.Insert(c);
			int scope = GetGame().ConfigGetInt(root + " " + c + " scope");
			string base;
			GetGame().ConfigGetBaseName(root + " " + c, base);
			Print("[AFProbe] class " + root + " " + c + " scope " + scope.ToString() + " base " + base);
		}
	}
}

void LogFrame(string tag)
{
	if (!g_W)
	{
		Print("[AFProbe] FAILED no weapon");
		return;
	}
	TStringArray mem = {"usti hlavne", "konec hlavne", "eye", "nabojnicestart", "nabojniceend", "bolt_axis", "trigger_axis", "magazine_axis", "magazine_axis2", "firemode_axis", "mag_release_axis", "charging_axis", "stock_axis", "lefthand", "righthand"};
	foreach (string m : mem)
	{
		if (g_W.MemoryPointExists(m))
			Print("[AFProbe] " + tag + " mem " + m + " = " + V(g_W.GetMemoryPointPos(m)));
		else
			Print("[AFProbe] " + tag + " mem " + m + " MISSING");
	}
	for (int i = 0; i < g_W.GetInventory().AttachmentCount(); i++)
	{
		EntityAI a = g_W.GetInventory().GetAttachmentFromIndex(i);
		vector o = g_W.WorldToModel(a.GetPosition());
		vector fwd = g_W.WorldToModel(a.ModelToWorld("0 0 1")) - o;
		vector up = g_W.WorldToModel(a.ModelToWorld("0 1 0")) - o;
		Print("[AFProbe] " + tag + " attachment " + a.GetType() + " at " + V(o) + " dir " + V(fwd) + " up " + V(up));
	}
	if (g_P)
	{
		TStringArray hb = {"RightHand", "LeftHand", "RightHandIndex1", "LeftHandIndex1", "Head", "Spine3"};
		foreach (string h : hb)
		{
			int hi = g_P.GetBoneIndexByName(h);
			if (hi >= 0)
				Print("[AFProbe] " + tag + " hand " + h + " = " + V(g_W.WorldToModel(g_P.GetBonePositionWS(hi))));
		}
	}
	vector box[2];
	g_W.GetCollisionBox(box);
	Print("[AFProbe] " + tag + " collision box " + V(box[0]) + " .. " + V(box[1]));
}

void LogConfig()
{
	string p = "CfgWeapons " + g_Rifle;
	TStringArray arr = new TStringArray;
	GetGame().ConfigGetTextArray(p + " attachments", arr);
	foreach (string slot : arr)
		Print("[AFProbe] slot " + slot);
	arr.Clear();
	GetGame().ConfigGetTextArray(p + " magazines", arr);
	Print("[AFProbe] magazines " + arr.ToString());
	arr.Clear();
	GetGame().ConfigGetTextArray(p + " modes", arr);
	Print("[AFProbe] modes " + arr.ToString());
	foreach (string m : arr)
	{
		float rel = GetGame().ConfigGetFloat(p + " " + m + " reloadTime");
		int burst = GetGame().ConfigGetInt(p + " " + m + " burst");
		Print("[AFProbe] mode " + m + " reloadTime " + rel.ToString() + " burst " + burst.ToString());
	}
	arr.Clear();
	GetGame().ConfigGetTextArray(p + " hiddenSelections", arr);
	Print("[AFProbe] hiddenSelections " + arr.ToString());
	string model;
	GetGame().ConfigGetText(p + " model", model);
	Print("[AFProbe] model " + model);
}

void main()
{
	GetGame().GetWorld().SetDate(2026, 6, 15, 12, 0);
	TStringArray w = new TStringArray;
	TStringArray mg = new TStringArray;
	ListClasses("CfgWeapons", w);
	ListClasses("CfgMagazines", mg);
	TStringArray veh = new TStringArray;
	ListClasses("CfgVehicles", veh);
	// The rifle: the first public (scope 2) weapon class whose name has SCAR and H (the SCAR-H).
	foreach (string c : w)
	{
		string lc = c;
		lc.ToLower();
		if (GetGame().ConfigGetInt("CfgWeapons " + c + " scope") == 2 && lc.Contains("h") && g_Rifle == "")
			g_Rifle = c;
	}
	if (g_Rifle == "" && w.Count() > 0)
		g_Rifle = w[0];
	TStringArray mags = new TStringArray;
	if (g_Rifle != "")
		GetGame().ConfigGetTextArray("CfgWeapons " + g_Rifle + " magazines", mags);
	if (mags.Count() > 0)
		g_Mag = mags[0];
	Print("[AFProbe] rifle " + g_Rifle + " magazine " + g_Mag);

	vector stand = "4660 0 10330";
	stand[1] = GetGame().SurfaceY(stand[0], stand[2]);
	g_P = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", stand, 0, "NONE"));
	GetGame().SelectPlayer(NULL, g_P);
	g_P.GetInventory().CreateInInventory("TShirt_Green");
	if (g_Rifle != "")
		g_W = Weapon_Base.Cast(g_P.GetHumanInventory().CreateInHands(g_Rifle));
	if (g_W && g_Mag != "")
		g_W.SpawnAmmo(g_Mag, WeaponWithAmmoFlags.CHAMBER | WeaponWithAmmoFlags.MAX_CAPACITY_MAG);
	// Fit a vanilla SCAR stock, to read where the stock slot sits.
	if (g_W)
	{
		foreach (string v : veh)
		{
			string lv = v;
			lv.ToLower();
			if (lv.Contains("bttstck") && GetGame().ConfigGetInt("CfgVehicles " + v + " scope") == 2)
			{
				EntityAI st = g_W.GetInventory().CreateAttachment(v);
				Print("[AFProbe] stock " + v + " fitted " + (st != null).ToString());
				if (st)
					break;
			}
		}
	}
	Print("[AFProbe] spawned " + g_Rifle + " " + (g_W != null).ToString());
}

class CustomMission: MissionGameplay
{
	override void OnInit()
	{
		super.OnInit();
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFRest, 15000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFRaise, 18000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFRaised, 22000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFQuit, 24000, false);
	}

	void AFRest()
	{
		if (g_Rifle != "")
			LogConfig();
		LogFrame("rest");
	}

	void AFRaise()
	{
		g_P.GetInputController().OverrideRaise(HumanInputControllerOverrideType.ENABLED, true);
		Print("[AFProbe] raising");
	}

	void AFRaised()
	{
		LogFrame("raised");
	}

	void AFQuit()
	{
		Print("[AFProbe] done");
		GetGame().RequestExit(0);
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
