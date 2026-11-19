// Offline test mission for the Allied Forces Weapons Pack. Runs only in DayZDiag_x64.exe on this
// PC; it never connects to a server. Start it with test\run_test.ps1.
//
// It lays every rifle out on the runway (both finishes, with attachments, damaged, ruined),
// puts an M41 in the player's hands, then flies a scripted camera through a list of shots,
// saves a screenshot of each and quits the game.

ref TStringArray g_ShotName = new TStringArray;
ref TVectorArray g_ShotCam = new TVectorArray;
ref TVectorArray g_ShotTarget = new TVectorArray;
ref TFloatArray g_ShotFov = new TFloatArray;
PlayerBase g_AFPlayer;
Weapon_Base g_AFHeld;

void AddShot(string name, vector cam, vector target, float fov)
{
	g_ShotName.Insert(name);
	g_ShotCam.Insert(cam);
	g_ShotTarget.Insert(target);
	g_ShotFov.Insert(fov);
}

// Each rifle stands on the ground along the X axis, 1.6 m from the next, all on one line.
// It is photographed from both sides, low down, and once close up.
EntityAI Lay(string type, vector origin, int index, string label)
{
	vector pos = origin;
	pos[0] = pos[0] + index * 1.6;
	pos[1] = GetGame().SurfaceY(pos[0], pos[2]);
	EntityAI item = EntityAI.Cast(GetGame().CreateObjectEx(type, pos, ECE_PLACE_ON_SURFACE));
	if (!item)
	{
		Print("[AFTest] FAILED to spawn " + type);
		return null;
	}
	Print("[AFTest] spawned " + type + " as " + label);
	vector p = item.GetPosition();
	vector mid = Vector(p[0], p[1] + 0.10, p[2]);
	AddShot(label + "_a", Vector(p[0], p[1] + 0.32, p[2] - 1.00), mid, 0.80);
	AddShot(label + "_b", Vector(p[0], p[1] + 0.32, p[2] + 1.00), mid, 0.80);
	AddShot(label + "_close", Vector(p[0] + 0.05, p[1] + 0.26, p[2] - 0.42), mid, 0.80);
	AddShot(label + "_top", Vector(p[0], p[1] + 0.95, p[2] - 0.25), mid, 0.80);
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
			for (int k = -2; k <= 14; k++)
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

	vector stand = Vector(pos[0] - 3.0, pos[1], pos[2]);
	PlayerBase player = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", stand, 0, "NONE"));
	GetGame().SelectPlayer(NULL, player);
	player.GetInventory().CreateInInventory("TShirt_Green");
	player.GetInventory().CreateInInventory("CargoPants_Green");
	player.GetInventory().CreateInInventory("AthleticShoes_Green");
	EntityAI held = player.GetHumanInventory().CreateInHands("AFM41_Pathfinder");
	g_AFPlayer = player;
	g_AFHeld = Weapon_Base.Cast(held);
	if (g_AFHeld && g_AFHeld.SpawnAmmo("Ammo_762x54", WeaponWithAmmoFlags.CHAMBER | WeaponWithAmmoFlags.MAX_CAPACITY_MAG))
		Print("[AFTest] held rifle loaded");
	else
		Print("[AFTest] FAILED to load the held rifle");
	if (held)
		Print("[AFTest] AFM41_Pathfinder in the player's hands");
	else
		Print("[AFTest] FAILED to put AFM41_Pathfinder in the player's hands");

	Lay("AF7_Vanguard", pos, 0, "af7");
	Lay("AF7_Vanguard_Gold", pos, 1, "af7_gold");
	Lay("AFM41_Pathfinder", pos, 2, "m41");
	Lay("AFM41_Pathfinder_Gold", pos, 3, "m41_gold");

	EntityAI kit = Lay("AFM41_Pathfinder", pos, 4, "m41_kit");
	Attach(kit, "PUScopeOptic");
	Attach(kit, "GhillieAtt_Mossy");
	Attach(kit, "Mosin_Bayonet");
	EntityAI kit2 = Lay("AF7_Vanguard", pos, 5, "af7_kit");
	Attach(kit2, "ACOGOptic");
	Attach(kit2, "M4_Suppressor");
	Attach(kit2, "UniversalLight");
	Attach(kit2, "Mag_STANAG_30Rnd");

	EntityAI worn = Lay("AFM41_Pathfinder", pos, 6, "m41_damaged");
	if (worn)
		worn.SetHealth01("", "", 0.4);
	EntityAI dead = Lay("AFM41_Pathfinder", pos, 7, "m41_ruined");
	if (dead)
		dead.SetHealth01("", "", 0.0);
	EntityAI worn2 = Lay("AF7_Vanguard", pos, 8, "af7_damaged");
	if (worn2)
		worn2.SetHealth01("", "", 0.4);
	EntityAI dead2 = Lay("AF7_Vanguard", pos, 9, "af7_ruined");
	if (dead2)
		dead2.SetHealth01("", "", 0.0);

	// The vanilla rifles they are built on, in the same light, to compare shine and colour.
	Lay("Mosin9130", pos, 10, "ref_mosin");
	Lay("M4A1", pos, 11, "ref_m4");

	// The player, then the first four rifles from further and further away (LODs).
	AddShot("player_side", Vector(stand[0] + 0.2, stand[1] + 1.3, stand[2] - 1.7), Vector(stand[0], stand[1] + 1.0, stand[2]), 0.9);
	AddShot("player_front", Vector(stand[0] + 1.7, stand[1] + 1.3, stand[2] - 0.3), Vector(stand[0], stand[1] + 1.0, stand[2]), 0.9);
	vector four = Vector(pos[0] + 2.4, pos[1] + 0.1, pos[2]);
	AddShot("lod_05m", Vector(four[0], four[1] + 1.2, four[2] - 5.0), four, 0.95);
	AddShot("lod_12m", Vector(four[0], four[1] + 1.4, four[2] - 12.0), four, 0.95);
	AddShot("lod_25m", Vector(four[0], four[1] + 1.6, four[2] - 25.0), four, 0.95);
	AddShot("lod_50m", Vector(four[0], four[1] + 1.6, four[2] - 50.0), four, 0.95);
	Print("[AFTest] " + g_ShotName.Count().ToString() + " shots planned");
}
class CustomMission: MissionGameplay
{
	protected Camera m_AFCam;
	protected int m_AFIndex = -1;

	override void OnInit()
	{
		super.OnInit();
		// First the firing test (raise, fire, work the bolt, a burst of pictures), then the still shots.
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFRaise, 20000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFFire, 24000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFCycle, 27500, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFLower, 32500, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFNext, 34000, false);
	}

	protected int m_AFBurst;
	protected string m_AFBurstName;

	void AFActionCam()
	{
		if (!m_AFCam)
		{
			m_AFCam = Camera.Cast(GetGame().CreateObject("staticcamera", g_AFPlayer.GetPosition(), true));
			m_AFCam.SetActive(true);
		}
		vector hand = g_AFPlayer.GetBonePositionWS(g_AFPlayer.GetBoneIndexByName("RightHand"));
		vector dir = g_AFPlayer.GetDirection();
		vector side = Vector(dir[2], 0, -dir[0]);          // the player's right
		m_AFCam.SetPosition(hand + side * 0.55 + Vector(0, 0.10, 0) + dir * 0.05);
		m_AFCam.LookAt(hand + dir * 0.08 + Vector(0, 0.04, 0));
		m_AFCam.SetFOV(0.75);
	}

	void AFBurstStart(string name, int frames)
	{
		m_AFBurstName = name;
		m_AFBurst = frames;
		AFBurstStep();
	}

	void AFBurstStep()
	{
		if (m_AFBurst <= 0)
			return;
		AFActionCam();
		Print("[AFTest] screenshot " + m_AFBurstName + "_" + (20 - m_AFBurst).ToString());
		m_AFBurst--;
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFBurstStep, 330, false);
	}

	void AFRaise()
	{
		g_AFPlayer.GetInputController().OverrideRaise(HumanInputControllerOverrideType.ENABLED, true);
		Print("[AFTest] raising the rifle");
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFBurstStart, 2500, false, "raised", 1);
	}

	void AFFire()
	{
		bool can = g_AFPlayer.GetWeaponManager().CanFire(g_AFHeld);
		Print("[AFTest] firing, CanFire=" + can.ToString());
		g_AFPlayer.GetWeaponManager().Fire(g_AFHeld);
		AFBurstStart("fire", 9);
	}

	void AFCycle()
	{
		bool can = g_AFPlayer.GetWeaponManager().CanEjectBulletVerified();
		Print("[AFTest] working the bolt, CanEject=" + can.ToString());
		g_AFPlayer.GetWeaponManager().EjectBulletVerified();
		AFBurstStart("bolt", 12);
	}

	void AFLower()
	{
		g_AFPlayer.GetInputController().OverrideRaise(HumanInputControllerOverrideType.DISABLED, false);
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
			m_AFCam.SetActive(true);
		}
		m_AFCam.SetPosition(g_ShotCam.Get(m_AFIndex));
		m_AFCam.LookAt(g_ShotTarget.Get(m_AFIndex));
		m_AFCam.SetFOV(g_ShotFov.Get(m_AFIndex));
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFShoot, 2500, false);
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
