// Offline test mission for the Allied Forces Weapons Pack. Runs only in DayZDiag_x64.exe on this
// PC; it never connects to a server. Start it with test\run_test.ps1.
//
// P08 version of AFWeaponsTest: it lays the AF P08 out on the runway (both finishes, without
// its magazine, the magazine alone, with each suppressor, damaged, ruined, and a vanilla P1),
// puts a P08 in the player's hands, raises it, works the action and swaps the magazine while
// taking pictures from both sides, then photographs the row and quits the game.
// Start it with: test\run_test.ps1 -Mission AFP08Test.ChernarusPlus

ref TStringArray g_ShotName = new TStringArray;
ref TVectorArray g_ShotCam = new TVectorArray;
ref TVectorArray g_ShotTarget = new TVectorArray;
ref TFloatArray g_ShotFov = new TFloatArray;
PlayerBase g_AFPlayer;
Weapon_Base g_AFHeld;
Magazine g_AFSpare;

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
	pos[0] = pos[0] + index * 0.8;
	pos[1] = GetGame().SurfaceY(pos[0], pos[2]);
	EntityAI item = EntityAI.Cast(GetGame().CreateObjectEx(type, pos, ECE_PLACE_ON_SURFACE));
	if (!item)
	{
		Print("[AFTest] FAILED to spawn " + type);
		return null;
	}
	Print("[AFTest] spawned " + type + " as " + label);
	vector p = item.GetPosition();
	vector mid = Vector(p[0], p[1] + 0.03, p[2]);
	AddShot(label + "_a", Vector(p[0], p[1] + 0.20, p[2] - 0.40), mid, 0.80);
	AddShot(label + "_b", Vector(p[0], p[1] + 0.20, p[2] + 0.40), mid, 0.80);
	AddShot(label + "_close", Vector(p[0] + 0.03, p[1] + 0.14, p[2] - 0.20), mid, 0.80);
	AddShot(label + "_top", Vector(p[0], p[1] + 0.42, p[2] - 0.06), mid, 0.80);
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
			for (int k = -2; k <= 8; k++)
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
	player.GetInventory().CreateInInventory("HighCapacityVest_Olive");
	EntityAI held = player.GetHumanInventory().CreateInHands("AF_P08");
	g_AFPlayer = player;
	g_AFHeld = Weapon_Base.Cast(held);
	if (g_AFHeld && g_AFHeld.SpawnAmmo("Mag_AFP08_8Rnd", WeaponWithAmmoFlags.CHAMBER | WeaponWithAmmoFlags.MAX_CAPACITY_MAG))
		Print("[AFTest] held gun loaded");
	else
		Print("[AFTest] FAILED to load the held gun");
	if (held)
		Print("[AFTest] AF_P08 in the player's hands");
	else
		Print("[AFTest] FAILED to put AF_P08 in the player's hands");
	g_AFSpare = Magazine.Cast(player.GetInventory().CreateInInventory("Mag_AFP08_8Rnd"));
	if (g_AFSpare)
		Print("[AFTest] spare magazine in the player's inventory");
	else
		Print("[AFTest] FAILED to give the player a spare magazine");

	EntityAI plain = Lay("AF_P08", pos, 0, "p08");
	Attach(plain, "Mag_AFP08_8Rnd");
	EntityAI gold = Lay("AF_P08_Gold", pos, 1, "p08_gold");
	Attach(gold, "Mag_AFP08_8Rnd");
	Lay("AF_P08", pos, 2, "p08_nomag");
	Lay("Mag_AFP08_8Rnd", pos, 3, "p08_mag");
	EntityAI kit = Lay("AF_P08", pos, 4, "p08_supp");
	Attach(kit, "Mag_AFP08_8Rnd");
	Attach(kit, "PistolSuppressor");
	EntityAI kit2 = Lay("AF_P08", pos, 5, "p08_bottle");
	Attach(kit2, "Mag_AFP08_8Rnd");
	Attach(kit2, "ImprovisedSuppressor");
	EntityAI worn = Lay("AF_P08", pos, 6, "p08_damaged");
	Attach(worn, "Mag_AFP08_8Rnd");
	if (worn)
		worn.SetHealth01("", "", 0.4);
	EntityAI dead = Lay("AF_P08", pos, 7, "p08_ruined");
	Attach(dead, "Mag_AFP08_8Rnd");
	if (dead)
		dead.SetHealth01("", "", 0.0);

	// The vanilla pistol it is built on, in the same light, to compare shine, colour and size.
	EntityAI ref = Lay("P1", pos, 8, "ref_p1");
	Attach(ref, "Mag_P1_8Rnd");	// The player, then the first four rifles from further and further away (LODs).
	AddShot("player_side", Vector(stand[0] + 0.2, stand[1] + 1.3, stand[2] - 1.7), Vector(stand[0], stand[1] + 1.0, stand[2]), 0.9);
	AddShot("player_front", Vector(stand[0] + 1.7, stand[1] + 1.3, stand[2] - 0.3), Vector(stand[0], stand[1] + 1.0, stand[2]), 0.9);
	vector four = Vector(pos[0] + 1.2, pos[1] + 0.05, pos[2]);
	AddShot("lod_02m", Vector(four[0], four[1] + 1.2, four[2] - 1.6), four, 0.95);
	AddShot("lod_05m", Vector(four[0], four[1] + 2.5, four[2] - 4.0), four, 0.95);
	AddShot("lod_12m", Vector(four[0], four[1] + 6.0, four[2] - 10.0), four, 0.95);
	AddShot("lod_25m", Vector(four[0], four[1] + 12.0, four[2] - 22.0), four, 0.95);
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
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFReload, 32500, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFLower, 41000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFNext, 42500, false);
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
		if (m_AFBurst % 2 == 0)
			side = side * -1.0;                             // every other picture from the left
		m_AFCam.SetPosition(hand + side * 0.42 + Vector(0, 0.10, 0) + dir * 0.06);
		m_AFCam.LookAt(hand + dir * 0.08 + Vector(0, 0.05, 0));
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
		Print("[AFTest] screenshot " + m_AFBurstName + "_" + (40 - m_AFBurst).ToString());
		m_AFBurst--;
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFBurstStep, 330, false);
	}

	void AFRaise()
	{
		g_AFPlayer.GetInputController().OverrideRaise(HumanInputControllerOverrideType.ENABLED, true);
		Print("[AFTest] raising the rifle");
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFBurstStart, 2500, false, "raised", 2);
	}

	void AFFire()
	{
		bool can = g_AFPlayer.GetWeaponManager().CanFire(g_AFHeld);
		Print("[AFTest] firing, CanFire=" + can.ToString());
		g_AFPlayer.GetWeaponManager().Fire(g_AFHeld);
		AFBurstStart("fire", 8);
	}

	void AFCycle()
	{
		bool can = g_AFPlayer.GetWeaponManager().CanEjectBulletVerified();
		Print("[AFTest] working the bolt, CanEject=" + can.ToString());
		g_AFPlayer.GetWeaponManager().EjectBulletVerified();
		AFBurstStart("bolt", 14);
	}

	void AFReload()
	{
		bool can = g_AFSpare && g_AFPlayer.GetWeaponManager().CanSwapMagazine(g_AFHeld, g_AFSpare);
		Print("[AFTest] swapping the magazine, CanSwap=" + can.ToString());
		if (g_AFSpare)
			g_AFPlayer.GetWeaponManager().SwapMagazine(g_AFSpare);
		AFBurstStart("reload", 20);
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
