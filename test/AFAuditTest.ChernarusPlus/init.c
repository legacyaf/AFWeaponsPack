// Offline test mission for the Allied Forces Weapons Pack. Runs only in DayZDiag_x64.exe on this
// PC; it never connects to a server.
//
// Surface-quality audit (2026-11-24): every AF weapon lies on the runway beside the vanilla weapon it
// is built on or closest to (AF-7 / M4A1, M41 / Mosin, MP40 / UMP-45, P08 / P1, StG 44 / AKM,
// M107A1 / SVD). Each is photographed from the side, close up and from the front in noon sun, and
// each pair side by side in noon sun, overcast, evening and morning light. Then the game quits.
// Start it with: test/run_test.ps1 -Mission AFAuditTest.ChernarusPlus -TimeoutSeconds 900

ref TStringArray g_ShotName = new TStringArray;
ref TVectorArray g_ShotCam = new TVectorArray;
ref TVectorArray g_ShotTarget = new TVectorArray;
ref TFloatArray g_ShotFov = new TFloatArray;
ref TFloatArray g_ShotHour = new TFloatArray;      // -1: leave the time of day as it is
ref TFloatArray g_ShotOvercast = new TFloatArray;  // -1: leave the sky as it is
PlayerBase g_AFPlayer;

void AddShot(string name, vector cam, vector target, float fov)
{
	g_ShotName.Insert(name);
	g_ShotCam.Insert(cam);
	g_ShotTarget.Insert(target);
	g_ShotFov.Insert(fov);
	g_ShotHour.Insert(-1);
	g_ShotOvercast.Insert(-1);
}

//! The same view as an earlier shot, under another light: `hour` (decimal) and `overcast` (0..1).
void AddLightShot(string name, string like, float hour, float overcast)
{
	int i = g_ShotName.Find(like);
	if (i < 0)
	{
		Print("[AFTest] FAILED light shot " + name + ": no shot " + like);
		return;
	}
	g_ShotName.Insert(name);
	g_ShotCam.Insert(g_ShotCam.Get(i));
	g_ShotTarget.Insert(g_ShotTarget.Get(i));
	g_ShotFov.Insert(g_ShotFov.Get(i));
	g_ShotHour.Insert(hour);
	g_ShotOvercast.Insert(overcast);
}

// Each weapon lies on the ground along the X axis (muzzle towards -X), 2.2 m from the next. `s` scales
// the camera distances to the weapon's length (1 = a rifle about 1.1 m long).
EntityAI Lay(string type, vector origin, int index, string label, float s)
{
	vector pos = origin;
	pos[0] = pos[0] + index * 2.2;
	pos[1] = GetGame().SurfaceY(pos[0], pos[2]);
	EntityAI item = EntityAI.Cast(GetGame().CreateObjectEx(type, pos, ECE_PLACE_ON_SURFACE));
	if (!item)
	{
		Print("[AFTest] FAILED to spawn " + type);
		return null;
	}
	Print("[AFTest] spawned " + type + " as " + label);
	vector p = item.GetPosition();
	vector mid = Vector(p[0] - 0.30 * s, p[1] + 0.04, p[2]);
	AddShot(label + "_a", Vector(mid[0], p[1] + 0.40 * s, p[2] - 1.55 * s), mid, 0.80);
	AddShot(label + "_close", Vector(p[0] + 0.05 * s, p[1] + 0.18 * s, p[2] - 0.42 * s), Vector(p[0], p[1] + 0.03, p[2]), 0.80);
	AddShot(label + "_front", Vector(p[0] - 1.25 * s, p[1] + 0.30 * s, p[2] - 0.55 * s), Vector(p[0] - 0.45 * s, p[1] + 0.04, p[2]), 0.80);
	return item;
}

void Attach(EntityAI parent, string type)
{
	if (!parent)
		return;
	EntityAI att = parent.GetInventory().CreateAttachment(type);
	if (att)
		Print("[AFTest] attached " + type + " to " + parent.GetType());
	else
		Print("[AFTest] FAILED to attach " + type + " to " + parent.GetType());
}

bool IsHard(float x, float z)
{
	string surface;
	GetGame().SurfaceGetType(x, z, surface);
	surface.ToLower();
	return surface.Contains("concrete") || surface.Contains("asphalt") || surface.Contains("tarmac") || surface.Contains("cp_con");
}

// A stretch of bare runway long enough for the row (grass hides rifles lying on it).
vector FindRunway(vector start)
{
	string here;
	GetGame().SurfaceGetType(start[0], start[2], here);
	Print("[AFTest] surface at the start point: " + here);
	for (int r = 0; r <= 400; r += 8)
	{
		for (int a = 0; a < 24; a++)
		{
			float x = start[0] + r * Math.Cos(a * 0.2618);
			float z = start[2] + r * Math.Sin(a * 0.2618);
			bool ok = true;
			for (int k = -2; k <= 18; k++)
			{
				if (!IsHard(x + k * 1.6, z - 2.5) || !IsHard(x + k * 1.6, z) || !IsHard(x + k * 1.6, z + 2.5))
				{
					ok = false;
					break;
				}
			}
			if (ok)
			{
				string found;
				GetGame().SurfaceGetType(x, z, found);
				Print("[AFTest] runway found " + r.ToString() + " m away, surface " + found);
				return Vector(x, GetGame().SurfaceY(x, z), z);
			}
		}
	}
	Print("[AFTest] FAILED to find bare runway; using the start point");
	return start;
}

void main()
{
	GetGame().GetWorld().SetDate(2026, 6, 15, 12, 0);
	Weather weather = GetGame().GetWeather();
	weather.GetOvercast().Set(0, 0, 0);
	weather.GetRain().Set(0, 0, 0);
	weather.GetFog().Set(0, 0, 0);

	vector pos = FindRunway("4660 0 10330");   // north-west airfield
	pos[1] = GetGame().SurfaceY(pos[0], pos[2]);
	vector stand = Vector(pos[0] - 6.0, pos[1], pos[2] + 6.0);
	PlayerBase player = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", stand, 0, "NONE"));
	GetGame().SelectPlayer(NULL, player);
	g_AFPlayer = player;

	// AF weapon, its magazine, size scale, then the vanilla weapon beside it and its magazine.
	string af[6] = {"AF7_Vanguard", "AFM41_Pathfinder", "AF_MP40", "AF_P08", "AF_StG44", "AF_M107A1"};
	string afMag[6] = {"Mag_STANAG_30Rnd", "", "Mag_AFMP40_32Rnd", "Mag_AFP08_8Rnd", "Mag_AFStG44_30Rnd", "Mag_AFM107_10Rnd"};
	string van[6] = {"M4A1", "Mosin9130", "UMP45", "P1", "AKM", "SVD"};
	string vanMag[6] = {"Mag_STANAG_30Rnd", "", "Mag_UMP_25Rnd", "Mag_P1_8Rnd", "Mag_AKM_30Rnd", "Mag_SVD_10Rnd"};
	string tag[6] = {"af7", "m41", "mp40", "p08", "stg44", "m107"};
	string vtag[6] = {"ref_m4", "ref_mosin", "ref_ump", "ref_p1", "ref_akm", "ref_svd"};
	float size[6] = {1.0, 1.15, 0.75, 0.35, 0.95, 1.3};
	float hours[3] = {12.0, 18.75, 6.5};
	float skies[3] = {0.95, 0.0, 0.25};
	string lights[3] = {"overcast", "evening", "morning"};
	for (int i = 0; i < 6; i++)
	{
		EntityAI a = Lay(af[i], pos, 2 * i, tag[i], size[i]);
		if (afMag[i] != "")
			Attach(a, afMag[i]);
		EntityAI v = Lay(van[i], pos, 2 * i + 1, vtag[i], size[i]);
		if (vanMag[i] != "")
			Attach(v, vanMag[i]);
		// The pair side by side, seen from the same side as the "_a" shots.
		float s = size[i];
		vector c = Vector(pos[0] + 2 * i * 2.2 + 1.1 - 0.30 * s, pos[1] + 0.04, pos[2]);
		c[1] = GetGame().SurfaceY(c[0], c[2]) + 0.04;
		AddShot("pair_" + tag[i], Vector(c[0], c[1] + 0.9 * s + 0.4, c[2] - 2.6 * s - 1.0), c, 0.80);
	}
	// The other lights last, one light at a time, so every noon shot above is taken at noon.
	for (int L = 0; L < 3; L++)
	{
		for (int k = 0; k < 6; k++)
			AddLightShot("light_" + lights[L] + "_" + tag[k], "pair_" + tag[k], hours[L], skies[L]);
	}
	Print("[AFTest] " + g_ShotName.Count().ToString() + " shots planned");
}

class CustomMission: MissionGameplay
{
	protected Camera m_AFCam;
	protected int m_AFIndex = -1;

	override void OnInit()
	{
		super.OnInit();
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFNext, 20000, false);
	}
	void AFNext()
	{
		m_AFIndex++;
		if (m_AFIndex >= g_ShotName.Count())
		{
			Print("[AFTest] all shots done");
			GetGame().RequestExit(0);
			return;
		}
		if (!m_AFCam)
		{
			m_AFCam = Camera.Cast(GetGame().CreateObject("staticcamera", g_ShotCam.Get(m_AFIndex), true));
		}
		m_AFCam.SetActive(true);
		m_AFCam.SetPosition(g_ShotCam.Get(m_AFIndex));
		m_AFCam.LookAt(g_ShotTarget.Get(m_AFIndex));
		m_AFCam.SetFOV(g_ShotFov.Get(m_AFIndex));
		int wait = 2500;
		float hour = g_ShotHour.Get(m_AFIndex);
		float sky = g_ShotOvercast.Get(m_AFIndex);
		if (hour >= 0 || sky >= 0)
		{
			if (hour >= 0)
			{
				int hh = Math.Floor(hour);
				GetGame().GetWorld().SetDate(2026, 6, 15, hh, Math.Round((hour - hh) * 60));
			}
			if (sky >= 0)
				GetGame().GetWeather().GetOvercast().Set(sky, 0, 0);
			Print("[AFTest] light " + g_ShotName.Get(m_AFIndex) + " hour=" + hour.ToString() + " overcast=" + sky.ToString());
			wait = 6000;           // let the sky and the lighting settle
		}
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFShoot, wait, false);
	}

	void AFShoot()
	{
		// The game's own MakeScreenshot() wrote no file here, so run_test.ps1 captures the window
		// when it sees this line in the script log. The view is held still long enough for that.
		Print("[AFTest] screenshot " + g_ShotName.Get(m_AFIndex));
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFNext, 1800, false);
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
