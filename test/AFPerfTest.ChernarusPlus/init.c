// Offline frame-rate and LOD test for the Allied Forces Weapons Pack. Runs only in DayZDiag_x64.exe
// on this PC; it never connects to a server.
// Start it with: test\run_test.ps1 -Mission AFPerfTest.ChernarusPlus -TimeoutSeconds 600
//
// Part 1 (frame rate; skipped when AF_PULL_ONLY is true): a 40 x 40 grid (1,600 pieces; fewer never pull this PC below its 180 fps cap) of one weapon is laid on the runway and the frame
// rate is averaged over four seconds from 15, 30 and 120 m. This is done for an empty runway,
// for each AF weapon and the vanilla weapon it is built on, bare and with their usual attachments, and for the magazines alone. Lines: "[AFPerf] <name> <metres> <fps> <frames>".
// Part 2 (LOD switching): one of each AF weapon and a vanilla Mosin side by side, photographed from
// 2 to 80 m. The white dot in the middle of every picture is the game's crosshair, not part of a
// weapon (it was mistaken for a fault on the M41 once); the row is laid out so no weapon sits under it.

const int AF_COLS = 40;
const int AF_ROWS = 40;
const float AF_DX = 0.95;
const float AF_DZ = 0.45;
const bool AF_PULL_ONLY = false;    // true: skip the frame-rate part and only take the pull-back pictures

vector g_AFOrigin;

bool IsHard(float x, float z)
{
	string surface;
	GetGame().SurfaceGetType(x, z, surface);
	surface.ToLower();
	return surface.Contains("concrete") || surface.Contains("asphalt") || surface.Contains("tarmac") || surface.Contains("cp_con");
}

vector FindRunway(vector start)
{
	for (int r = 0; r <= 400; r += 8)
	{
		for (int a = 0; a < 24; a++)
		{
			float x = start[0] + r * Math.Cos(a * 0.2618);
			float z = start[2] + r * Math.Sin(a * 0.2618);
			bool ok = true;
			for (int k = -1; k <= 8; k++)
			{
				if (!IsHard(x + k * 1.9, z - 1.0) || !IsHard(x + k * 1.9, z + 3.5) || !IsHard(x + k * 1.9, z + 7.5))
				{
					ok = false;
					break;
				}
			}
			if (ok)
			{
				Print("[AFTest] runway found " + r.ToString() + " m away");
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

	g_AFOrigin = FindRunway("4660 0 10330");   // north-west airfield
	vector stand = Vector(g_AFOrigin[0] - 6.0, g_AFOrigin[1], g_AFOrigin[2] - 6.0);
	PlayerBase player = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", stand, 0, "NONE"));
	GetGame().SelectPlayer(NULL, player);
}

class CustomMission: MissionGameplay
{
	protected Camera m_Cam;
	protected ref array<Object> m_Items = new array<Object>;
	protected ref TStringArray m_Groups = new TStringArray;
	protected ref TFloatArray m_Dists = new TFloatArray;
	protected ref TFloatArray m_Pull = new TFloatArray;
	protected int m_Group = -1;
	protected int m_Dist = 0;
	protected int m_Phase = 0;          // 0 waiting to start, 1 settling, 2 measuring, 3 pull-back pictures, 4 done
	protected float m_T0;
	protected int m_Frames;
	protected float m_Worst;
	protected int m_PullIndex = -1;
	protected bool m_PullShot;

	override void OnInit()
	{
		super.OnInit();
		// A name ending in "+" is spawned with its usual attachments (see Dress), otherwise bare.
		string list = "empty AF7_Vanguard AF7_Vanguard+ M4A1 M4A1+ AFM41_Pathfinder Mosin9130 AF_MP40 AF_MP40+ UMP45 UMP45+ Mag_AFMP40_32Rnd Mag_UMP_25Rnd Mag_STANAG_30Rnd empty";
		if (AF_PULL_ONLY)
			list = "";
		list.Split(" ", m_Groups);
		m_Dists.Insert(15);
		m_Dists.Insert(30);
		
		m_Dists.Insert(120);
		
		m_Pull.Insert(2);
		m_Pull.Insert(3);
		m_Pull.Insert(4);
		m_Pull.Insert(6);
		m_Pull.Insert(8);
		m_Pull.Insert(11);
		m_Pull.Insert(15);
		m_Pull.Insert(20);
		m_Pull.Insert(28);
		m_Pull.Insert(40);
		m_Pull.Insert(55);
		m_Pull.Insert(80);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFStart, 20000, false);
	}

	vector Centre()
	{
		float x = g_AFOrigin[0] + (AF_COLS - 1) * AF_DX * 0.5;
		float z = g_AFOrigin[2] + (AF_ROWS - 1) * AF_DZ * 0.5;
		return Vector(x, GetGame().SurfaceY(x, z) + 0.1, z);
	}

	void Aim(vector target, float d)
	{
		vector pos = Vector(target[0], target[1] + d * 0.57, target[2] - d * 0.82);
		if (!m_Cam)
		{
			m_Cam = Camera.Cast(GetGame().CreateObject("staticcamera", pos, true));
			m_Cam.SetActive(true);
		}
		m_Cam.SetPosition(pos);
		m_Cam.LookAt(target);
		m_Cam.SetFOV(0.95);
	}

	void Dress(EntityAI item, string type)
	{
		if (type == "AF7_Vanguard")
			item.GetInventory().CreateAttachment("Mag_STANAG_30Rnd");
		if (type == "M4A1")
		{
			item.GetInventory().CreateAttachment("M4_RISHndgrd");
			item.GetInventory().CreateAttachment("M4_OEBttstck");
			item.GetInventory().CreateAttachment("Mag_STANAG_30Rnd");
		}
		if (type == "AF_MP40")
			item.GetInventory().CreateAttachment("Mag_AFMP40_32Rnd");
		if (type == "UMP45")
			item.GetInventory().CreateAttachment("Mag_UMP_25Rnd");
	}

	void Clear()
	{
		foreach (Object o : m_Items)
		{
			if (o)
				GetGame().ObjectDelete(o);
		}
		m_Items.Clear();
	}

	void Fill(string type)
	{
		Clear();
		bool dressed = type.Contains("+");
		type.Replace("+", "");
		if (type == "empty")
			return;
		for (int r = 0; r < AF_ROWS; r++)
		{
			for (int c = 0; c < AF_COLS; c++)
			{
				vector p = Vector(g_AFOrigin[0] + c * AF_DX, 0, g_AFOrigin[2] + r * AF_DZ);
				p[1] = GetGame().SurfaceY(p[0], p[2]);
				EntityAI item = EntityAI.Cast(GetGame().CreateObjectEx(type, p, ECE_PLACE_ON_SURFACE));
				if (item)
				{
					if (dressed)
						Dress(item, type);
					m_Items.Insert(item);
				}
			}
		}
		Print("[AFTest] spawned " + m_Items.Count().ToString() + " x " + type);
	}

	void AFStart()
	{
		NextGroup();
	}

	void NextGroup()
	{
		m_Group++;
		if (m_Group >= m_Groups.Count())
		{
			StartPull();
			return;
		}
		Fill(m_Groups.Get(m_Group));
		m_Dist = 0;
		Settle();
	}

	void Settle()
	{
		Aim(Centre(), m_Dists.Get(m_Dist));
		m_Phase = 1;
		m_T0 = GetGame().GetTickTime();
	}

	void StartPull()
	{
		Clear();
		vector c = Centre();
		TStringArray three = {"AF7_Vanguard", "AFM41_Pathfinder", "AF_MP40", "Mosin9130"};   // the Mosin for comparison
		for (int i = 0; i < three.Count(); i++)
		{
			vector p = Vector(c[0] + (i - 1.5) * 1.3, 0, c[2]);
			p[1] = GetGame().SurfaceY(p[0], p[2]);
			EntityAI item = EntityAI.Cast(GetGame().CreateObjectEx(three.Get(i), p, ECE_PLACE_ON_SURFACE));
			if (item)
			{
				Dress(item, three.Get(i));
				m_Items.Insert(item);
			}
		}
		m_Phase = 3;
		m_PullIndex = -1;
		NextPull();
	}

	void NextPull()
	{
		m_PullIndex++;
		if (m_PullIndex >= m_Pull.Count())
		{
			m_Phase = 4;
			Print("[AFTest] all shots done");
			GetGame().RequestExit(0);
			return;
		}
		Aim(Centre(), m_Pull.Get(m_PullIndex));
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.PullShot, 2200, false);
	}

	void PullShot()
	{
		int d = m_Pull.Get(m_PullIndex);
		string n = d.ToString();
		if (d < 10)
			n = "0" + n;
		Print("[AFTest] screenshot pull_" + n + "m");
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.NextPull, 1500, false);
	}

	override void OnUpdate(float timeslice)
	{
		super.OnUpdate(timeslice);
		float now = GetGame().GetTickTime();
		if (m_Phase == 1 && now - m_T0 > 2.5)
		{
			m_Phase = 2;
			m_T0 = now;
			m_Frames = 0;
			m_Worst = 0;
		}
		else if (m_Phase == 2)
		{
			m_Frames++;
			if (timeslice > m_Worst)
				m_Worst = timeslice;
			if (now - m_T0 >= 4.0)
			{
				float fps = m_Frames / (now - m_T0);
				int d = m_Dists.Get(m_Dist);
				Print("[AFPerf] " + m_Groups.Get(m_Group) + " " + d.ToString() + " " + fps.ToString() + " " + m_Frames.ToString() + " worst_ms " + (m_Worst * 1000).ToString());
				if (m_Dist == 1)
					Print("[AFTest] screenshot perf_" + m_Group.ToString() + "_" + m_Groups.Get(m_Group));
				m_Dist++;
				if (m_Dist >= m_Dists.Count())
				{
					m_Phase = 0;
					GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.NextGroup, 600, false);
				}
				else
				{
					Settle();
				}
			}
		}
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
