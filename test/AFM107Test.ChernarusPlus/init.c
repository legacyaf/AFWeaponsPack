// Offline test mission for the Allied Forces Weapons Pack. Runs only in DayZDiag_x64.exe on this
// PC; it never connects to a server. Start it with test\run_test.ps1.
//
// AF M107A1 version: lays the M107A1 out on the runway (with its magazine, without, the magazine
// alone, damaged, and a vanilla SVD with its PSO-1 to compare), puts a loaded M107A1 in the player's
// hands, raises it, fires and swaps the magazine while taking pictures from both sides, then aims
// down the built-in scope from the player's own camera (so the scripted scope view shows) at 6x and
// 12x, photographs the row in four lights and quits the game.
// Start it with: test\run_test.ps1 -Mission AFM107Test.ChernarusPlus

ref TStringArray g_ShotName = new TStringArray;
ref TVectorArray g_ShotCam = new TVectorArray;
ref TVectorArray g_ShotTarget = new TVectorArray;
ref TFloatArray g_ShotFov = new TFloatArray;
ref TFloatArray g_ShotHour = new TFloatArray;      // -1: leave the time of day as it is
ref TFloatArray g_ShotOvercast = new TFloatArray;  // -1: leave the sky as it is
PlayerBase g_AFPlayer;
Weapon_Base g_AFHeld;
Magazine g_AFSpare;

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

// Each rifle lies on the ground along the X axis (muzzle towards -X), 2.2 m from the next.
EntityAI Lay(string type, vector origin, int index, string label)
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
	vector mid = Vector(p[0] - 0.30, p[1] + 0.04, p[2]);
	AddShot(label + "_a", Vector(mid[0], p[1] + 0.40, p[2] - 1.55), mid, 0.80);
	AddShot(label + "_b", Vector(mid[0], p[1] + 0.40, p[2] + 1.55), mid, 0.80);
	AddShot(label + "_close", Vector(p[0] + 0.05, p[1] + 0.18, p[2] - 0.42), Vector(p[0], p[1] + 0.05, p[2]), 0.80);
	AddShot(label + "_front", Vector(p[0] - 1.25, p[1] + 0.30, p[2] - 0.55), Vector(p[0] - 0.45, p[1] + 0.05, p[2]), 0.80);
	AddShot(label + "_top", Vector(mid[0], p[1] + 1.40, p[2] - 0.10), mid, 0.80);
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

	vector stand = Vector(pos[0] - 4.0, pos[1], pos[2]);
	PlayerBase player = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", stand, 0, "NONE"));
	GetGame().SelectPlayer(NULL, player);
	player.GetInventory().CreateInInventory("TShirt_Green");
	player.GetInventory().CreateInInventory("CargoPants_Green");
	player.GetInventory().CreateInInventory("AthleticShoes_Green");
	player.GetInventory().CreateInInventory("HighCapacityVest_Olive");
	EntityAI held = player.GetHumanInventory().CreateInHands("AF_M107A1");
	g_AFPlayer = player;
	g_AFHeld = Weapon_Base.Cast(held);
	if (g_AFHeld && g_AFHeld.SpawnAmmo("Mag_AFM107_10Rnd", WeaponWithAmmoFlags.CHAMBER | WeaponWithAmmoFlags.MAX_CAPACITY_MAG))
		Print("[AFTest] held gun loaded");
	else
		Print("[AFTest] FAILED to load the held gun");
	if (held)
		Print("[AFTest] AF_M107A1 in the player's hands");
	else
		Print("[AFTest] FAILED to put AF_M107A1 in the player's hands");
	g_AFSpare = Magazine.Cast(player.GetInventory().CreateInInventory("Mag_AFM107_10Rnd"));
	if (g_AFSpare)
		Print("[AFTest] spare magazine in the player's inventory");
	else
		Print("[AFTest] FAILED to give the player a spare magazine");

	EntityAI rifle = Lay("AF_M107A1", pos, 0, "m107");
	Attach(rifle, "Mag_AFM107_10Rnd");
	Lay("AF_M107A1", pos, 1, "m107_nomag");
	Lay("Mag_AFM107_10Rnd", pos, 2, "m107_mag");
	EntityAI worn = Lay("AF_M107A1", pos, 3, "m107_damaged");
	Attach(worn, "Mag_AFM107_10Rnd");
	if (worn)
		worn.SetHealth01("", "", 0.4);
	// The vanilla rifle it is built on, in the same light, to compare shine, colour and size.
	EntityAI vanilla = Lay("SVD", pos, 4, "ref_svd");
	Attach(vanilla, "Mag_SVD_10Rnd");
	Attach(vanilla, "PSO1Optic");

	AddShot("player_side", Vector(stand[0] + 0.2, stand[1] + 1.3, stand[2] - 2.0), Vector(stand[0], stand[1] + 1.0, stand[2]), 0.9);
	AddShot("player_front", Vector(stand[0] + 2.0, stand[1] + 1.3, stand[2] - 0.3), Vector(stand[0], stand[1] + 1.0, stand[2]), 0.9);
	vector two = Vector(pos[0] + 1.1, pos[1] + 0.05, pos[2]);
	AddShot("lod_05m", Vector(two[0], two[1] + 2.5, two[2] - 4.0), two, 0.95);
	AddShot("lod_12m", Vector(two[0], two[1] + 6.0, two[2] - 10.0), two, 0.95);
	AddShot("lod_25m_zoom", Vector(two[0], two[1] + 12.0, two[2] - 22.0), two, 0.10);
	float hours[3] = {12.0, 18.75, 6.5};
	float skies[3] = {0.95, 0.0, 0.25};
	string tags[3] = {"overcast", "evening", "morning"};
	for (int L = 0; L < 3; L++)
	{
		AddLightShot("light_" + tags[L] + "_m107_close", "m107_close", hours[L], skies[L]);
		AddLightShot("light_" + tags[L] + "_m107_a", "m107_a", hours[L], skies[L]);
		AddLightShot("light_" + tags[L] + "_svd_a", "ref_svd_a", hours[L], skies[L]);
	}
	Print("[AFTest] " + g_ShotName.Count().ToString() + " shots planned");
}
class CustomMission: MissionGameplay
{
	protected Camera m_AFCam;
	EntityAI m_AFCamEnt;
	string m_AFCamFrom, m_AFCamTo;
	float m_AFCamFov;
	int m_AFTrackUntil;
	protected int m_AFIndex = -1;

	override void OnInit()
	{
		super.OnInit();
		// First the firing test (raise, fire, a burst of pictures, magazine swap), then the scope view from
		// the player's own camera at 6x and 12x, then the still shots.
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFRaise, 20000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFFire, 24000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFReload, 30000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFAim, 42000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFAimShot, 45500, false, "ads_6x");
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFZoom, 47000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFAimShot, 49500, false, "ads_12x");
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFUnaim, 51000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFLower, 53000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFNext, 55000, false);
	}

	void AFShotNamed(string name)
	{
		Print("[AFTest] screenshot " + name);
	}

	//! Aim down the scope as a player does: ironsights on, which on this rifle goes straight to the
	//! scope (the game's own path). The game's camera stays active (no still camera), so the
	//! scripted scope view (reticle, mask, zoom, range) is in the picture.
	void AFAim()
	{
		// Deleted, not just switched off: switched off, the still camera kept the view (first run).
		if (m_AFCam)
		{
			m_AFCam.SetActive(false);
			GetGame().ObjectDelete(m_AFCam);
			m_AFCam = null;
		}
		Print("[AFTest] aiming down the scope");
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFHoldAim, 100, true);
	}

	//! Every 0.1 s until AFUnaim: ironsights on and, if the game has not gone into the scope, into it.
	void AFHoldAim()
	{
		ItemOptics optic = ItemOptics.Cast(g_AFHeld.FindAttachmentBySlotName("weaponOpticsAFM107"));
		if (!g_AFPlayer.IsInIronsights())
			g_AFPlayer.SetIronsights(true);
		if (optic && !optic.IsInOptics())
			g_AFPlayer.SwitchOptics(optic, true);
	}

	void AFAimShot(string name)
	{
		ItemOptics optic = ItemOptics.Cast(g_AFHeld.FindAttachmentBySlotName("weaponOpticsAFM107"));
		bool inOptics = optic && optic.IsInOptics();
		int step = -1;
		if (optic)
			step = optic.GetStepFOVIndex();
		Print("[AFTest] " + name + " inOptics=" + inOptics.ToString() + " step=" + step.ToString() + " camera=" + GetGame().GetCurrentCameraPosition().ToString());
		Print("[AFTest] screenshot " + name);
	}

	void AFZoom()
	{
		ItemOptics optic = ItemOptics.Cast(g_AFHeld.FindAttachmentBySlotName("weaponOpticsAFM107"));
		if (optic)
			optic.SetStepFOVIndex(3);
	}

	void AFUnaim()
	{
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).Remove(this.AFHoldAim);
		g_AFPlayer.SetIronsights(false);
		ItemOptics optic = ItemOptics.Cast(g_AFHeld.FindAttachmentBySlotName("weaponOpticsAFM107"));
		if (optic && optic.IsInOptics())
			g_AFPlayer.SwitchOptics(optic, false);
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
