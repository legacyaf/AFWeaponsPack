// Offline lighting-series mission for the Allied Forces Weapons Pack. Runs only in DayZDiag_x64.exe on
// this PC; it never connects to a server.
//
// Judges the look of The PeaceKeeper beside the vanilla SCAR-H it is built on: both rifles lie 0.6 m
// apart on the bare runway (placed and oriented the way AFPKTest places them), each with its stock and
// a 20-round magazine. Six views are taken in four lights (noon clear, overcast, evening, night):
// pair, pk_close, pk_lower, pk_stock, pk_front, scarh_close, named like noon_pair, night_pk_close.
// run_test.ps1 saves a window picture for every "[AFTest] screenshot <name>" line.
// Start it with: test\run_test.ps1 -Mission AFPKLight.ChernarusPlus -TimeoutSeconds 200

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

//! A shot that also sets the light before it is taken: `hour` (decimal) and `overcast` (0..1).
void AddLightShot(string name, vector cam, vector target, float fov, float hour, float overcast)
{
	AddShot(name, cam, target, fov);
	int last = g_ShotName.Count() - 1;
	g_ShotHour.Set(last, hour);
	g_ShotOvercast.Set(last, overcast);
}

//! Lays a rifle on the ground at `pos` (muzzle towards -X, as in AFPKTest) and returns it.
EntityAI LayAt(string type, vector pos, string label)
{
	pos[1] = GetGame().SurfaceY(pos[0], pos[2]);
	EntityAI item = EntityAI.Cast(GetGame().CreateObjectEx(type, pos, ECE_PLACE_ON_SURFACE));
	if (!item)
	{
		Print("[AFTest] FAILED to spawn " + type);
		return null;
	}
	Print("[AFTest] spawned " + type + " as " + label);
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

//! The six views of one light. The first carries the light change, the others reuse it.
//! `p` is the PeaceKeeper's position, `s` the vanilla rifle's (0.6 m further along +Z).
void AddSet(string tag, float hour, float overcast, vector p, vector s)
{
	vector mid = Vector(p[0] - 0.30, p[1] + 0.04, p[2] + 0.30);
	AddLightShot(tag + "_pair", Vector(mid[0], p[1] + 0.95, p[2] - 1.20), mid, 0.80, hour, overcast);
	AddShot(tag + "_pk_close", Vector(p[0] + 0.05, p[1] + 0.18, p[2] - 0.42), Vector(p[0], p[1] + 0.05, p[2]), 0.80);
	AddShot(tag + "_pk_lower", Vector(p[0] + 0.12, p[1] + 0.22, p[2] - 0.27), Vector(p[0] + 0.10, p[1] + 0.02, p[2]), 0.80);
	AddShot(tag + "_pk_stock", Vector(p[0] + 0.55, p[1] + 0.20, p[2] - 0.40), Vector(p[0] + 0.50, p[1] + 0.04, p[2]), 0.80);
	AddShot(tag + "_pk_front", Vector(p[0] - 1.25, p[1] + 0.30, p[2] - 0.55), Vector(p[0] - 0.45, p[1] + 0.05, p[2]), 0.80);
	// The vanilla receiver from the same distance as pk_close; the camera stands over the gap between
	// the rifles and looks down so the PeaceKeeper does not hide it.
	AddShot(tag + "_scarh_close", Vector(s[0] + 0.05, s[1] + 0.40, s[2] - 0.22), Vector(s[0], s[1] + 0.05, s[2]), 0.80);
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
			for (int k = -2; k <= 12; k++)
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

	// The mission needs a player to run; he stands well away from the rifles, out of every view.
	vector stand = Vector(pos[0] - 6.0, pos[1], pos[2] - 3.0);
	PlayerBase player = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", stand, 0, "NONE"));
	GetGame().SelectPlayer(NULL, player);
	g_AFPlayer = player;

	vector posPK = pos;
	vector posScar = Vector(pos[0], pos[1], pos[2] + 0.6);
	EntityAI rifle = LayAt("AF_PeaceKeeper", posPK, "pk");
	Attach(rifle, "AF_PeaceKeeperStock");
	Attach(rifle, "Mag_SCARH_20Rnd");
	EntityAI vanilla = LayAt("SCARH", posScar, "ref_scarh");
	Attach(vanilla, "SCAR_StockBttstck");
	Attach(vanilla, "Mag_SCARH_20Rnd");
	Attach(vanilla, "Scarh_Front_Sight");

	vector p = posPK;
	if (rifle)
		p = rifle.GetPosition();
	vector s = posScar;
	if (vanilla)
		s = vanilla.GetPosition();

	AddSet("noon", 12.0, 0.0, p, s);
	AddSet("overcast", 12.0, 1.0, p, s);
	AddSet("evening", 18.5, 0.0, p, s);
	AddSet("night", 23.5, 0.0, p, s);
	Print("[AFTest] " + g_ShotName.Count().ToString() + " shots planned");
}

class CustomMission: MissionGameplay
{
	protected Camera m_AFCam;
	protected int m_AFIndex = -1;

	override void OnInit()
	{
		super.OnInit();
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFNext, 10000, false);
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
		int wait = 1200;
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
			wait = 5000;           // let the sky and the lighting settle
		}
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFShoot, wait, false);
	}

	void AFShoot()
	{
		// run_test.ps1 captures the window when it sees this line in the script log; the view is held
		// still long enough for that.
		Print("[AFTest] screenshot " + g_ShotName.Get(m_AFIndex));
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFNext, 1300, false);
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
