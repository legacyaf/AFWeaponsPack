// Offline test mission for the Allied Forces Weapons Pack. Runs only in DayZDiag_x64.exe on this
// PC; it never connects to a server. Start it with test\run_test.ps1.
//
// StG 44 version of AFWeaponsTest: it lays the AF StG 44 out on the runway (both finishes, without
// its magazine, the magazine alone, the ZF4 scope alone, with the scope, with each suppressor,
// damaged, ruined, and a vanilla AKM), puts a loaded StG 44 in the player's hands, raises it,
// fires, works the action and swaps the magazine while taking pictures from both sides, then
// takes the iron-sight and scope views, photographs the row and quits the game.
// Start it with: test\run_test.ps1 -Mission AFStG44Test.ChernarusPlus

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
	pos[0] = pos[0] + index * 1.4;
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
	AddShot(label + "_a", Vector(p[0], p[1] + 0.30, p[2] - 0.95), mid, 0.80);
	AddShot(label + "_b", Vector(p[0], p[1] + 0.30, p[2] + 0.95), mid, 0.80);
	AddShot(label + "_close", Vector(p[0] + 0.05, p[1] + 0.16, p[2] - 0.38), mid, 0.80);
	AddShot(label + "_top", Vector(p[0], p[1] + 0.95, p[2] - 0.10), mid, 0.80);
	AddShot(label + "_low", Vector(p[0] + 0.30, p[1] + 0.03, p[2] - 0.40), Vector(p[0], p[1] + 0.02, p[2]), 0.80);
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

	vector stand = Vector(pos[0] - 3.0, pos[1], pos[2]);
	PlayerBase player = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", stand, 0, "NONE"));
	GetGame().SelectPlayer(NULL, player);
	player.GetInventory().CreateInInventory("TShirt_Green");
	player.GetInventory().CreateInInventory("CargoPants_Green");
	player.GetInventory().CreateInInventory("AthleticShoes_Green");
	player.GetInventory().CreateInInventory("HighCapacityVest_Olive");
	EntityAI held = player.GetHumanInventory().CreateInHands("AF_StG44");
	g_AFPlayer = player;
	g_AFHeld = Weapon_Base.Cast(held);
	if (g_AFHeld && g_AFHeld.SpawnAmmo("Mag_AFStG44_30Rnd", WeaponWithAmmoFlags.CHAMBER | WeaponWithAmmoFlags.MAX_CAPACITY_MAG))
		Print("[AFTest] held gun loaded");
	else
		Print("[AFTest] FAILED to load the held gun");
	if (held)
		Print("[AFTest] AF_StG44 in the player's hands");
	else
		Print("[AFTest] FAILED to put AF_StG44 in the player's hands");
	g_AFSpare = Magazine.Cast(player.GetInventory().CreateInInventory("Mag_AFStG44_30Rnd"));
	if (g_AFSpare)
		Print("[AFTest] spare magazine in the player's inventory");
	else
		Print("[AFTest] FAILED to give the player a spare magazine");

	EntityAI plain = Lay("AF_StG44", pos, 0, "stg");
	Attach(plain, "Mag_AFStG44_30Rnd");
	EntityAI gold = Lay("AF_StG44_Gold", pos, 1, "stg_gold");
	Attach(gold, "Mag_AFStG44_30Rnd");
	Attach(gold, "AF_ZF4Optic");
	Lay("AF_StG44", pos, 2, "stg_nomag");
	Lay("Mag_AFStG44_30Rnd", pos, 3, "stg_mag");
	Lay("AF_ZF4Optic", pos, 4, "stg_zf4");
	EntityAI scoped = Lay("AF_StG44", pos, 5, "stg_scope");
	Attach(scoped, "Mag_AFStG44_30Rnd");
	Attach(scoped, "AF_ZF4Optic");
	EntityAI kit = Lay("AF_StG44", pos, 6, "stg_supp");
	Attach(kit, "Mag_AFStG44_30Rnd");
	Attach(kit, "AK_Suppressor");
	EntityAI kit2 = Lay("AF_StG44", pos, 7, "stg_bottle");
	Attach(kit2, "Mag_AFStG44_30Rnd");
	Attach(kit2, "ImprovisedSuppressor");
	EntityAI worn = Lay("AF_StG44", pos, 8, "stg_damaged");
	Attach(worn, "Mag_AFStG44_30Rnd");
	if (worn)
		worn.SetHealth01("", "", 0.4);
	EntityAI dead = Lay("AF_StG44", pos, 9, "stg_ruined");
	Attach(dead, "Mag_AFStG44_30Rnd");
	if (dead)
		dead.SetHealth01("", "", 0.0);
	// Things that must NOT fit: a vanilla AKM magazine and a vanilla scope.
	EntityAI wrong = Lay("AF_StG44", pos, 10, "stg_wrong");
	Attach(wrong, "Mag_AKM_30Rnd");
	Attach(wrong, "PUScopeOptic");

	// The vanilla rifle it is built on, in the same light, to compare shine, colour and size.
	EntityAI vanilla = Lay("AKM", pos, 11, "ref_akm");
	Attach(vanilla, "Mag_AKM_30Rnd");
	// The player, then the first four rifles from further and further away (LODs).
	AddShot("player_side", Vector(stand[0] + 0.2, stand[1] + 1.3, stand[2] - 1.7), Vector(stand[0], stand[1] + 1.0, stand[2]), 0.9);
	AddShot("player_front", Vector(stand[0] + 1.7, stand[1] + 1.3, stand[2] - 0.3), Vector(stand[0], stand[1] + 1.0, stand[2]), 0.9);
	vector four = Vector(pos[0] + 2.1, pos[1] + 0.05, pos[2]);
	AddShot("lod_02m", Vector(four[0], four[1] + 1.2, four[2] - 1.6), four, 0.95);
	AddShot("lod_05m", Vector(four[0], four[1] + 2.5, four[2] - 4.0), four, 0.95);
	AddShot("lod_12m", Vector(four[0], four[1] + 6.0, four[2] - 10.0), four, 0.95);
	AddShot("lod_25m", Vector(four[0], four[1] + 12.0, four[2] - 22.0), four, 0.95);
	// The same 25 m, zoomed in: the far model large enough to judge its shading (if the game picks the
	// level by distance; if it allows for the zoom, this shows a nearer level instead).
	AddShot("lod_25m_zoom", Vector(four[0], four[1] + 12.0, four[2] - 22.0), four, 0.10);
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
		// First the firing test (raise, fire, work the bolt, a burst of pictures), then the still shots.
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFRaise, 20000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFFire, 24000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFCycle, 27500, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFReload, 32500, false);
		// Sight pictures while the rifle is still raised: iron sights, then the ZF4 fitted and its view.
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFIronView, 40000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFFitScope, 43000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFScopeView, 45000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFLower, 49000, false);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFNext, 50500, false);
	}

	//! A still camera at a memory point of `ent`, looking from `from` towards `towards` (both memory points).
	void AFPointCam(EntityAI ent, string from, string towards, float fov, string name)
	{
		if (!ent || !ent.MemoryPointExists(from) || !ent.MemoryPointExists(towards))
		{
			Print("[AFTest] FAILED sight view " + name + ": memory point missing");
			return;
		}
		m_AFCamEnt = ent;
		m_AFCamFrom = from;
		m_AFCamTo = towards;
		m_AFCamFov = fov;
		AFPlaceCam(name);
		m_AFTrackUntil = GetGame().GetTime() + 2200;       // follow the eye point until after the picture
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFTrackCam, 0, true);
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFShotNamed, 1500, false, name);
	}

	//! Every frame while a sight picture is being taken: keep the camera on the swaying weapon's eye point.
	void AFTrackCam()
	{
		if (!m_AFCamEnt || !m_AFCam || GetGame().GetTime() > m_AFTrackUntil)
		{
			GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).Remove(this.AFTrackCam);
			return;
		}
		vector eye = m_AFCamEnt.ModelToWorld(m_AFCamEnt.GetMemoryPointPos(m_AFCamFrom));
		vector ahead = m_AFCamEnt.ModelToWorld(m_AFCamEnt.GetMemoryPointPos(m_AFCamTo));
		m_AFCam.SetPosition(eye);
		m_AFCam.LookAt(eye + vector.Direction(eye, ahead).Normalized() * 20.0);
	}

	//! Puts the still camera on the memory point as the weapon is now. The held weapon sways, so AFTrackCam
	//! repeats this every frame until the picture is taken: placed once, 1.5 s before the picture, the camera
	//! was off the eye point by the sway and the front post hid behind the rear notch (2026-11-23).
	void AFPlaceCam(string name)
	{
		vector eye = m_AFCamEnt.ModelToWorld(m_AFCamEnt.GetMemoryPointPos(m_AFCamFrom));
		vector ahead = m_AFCamEnt.ModelToWorld(m_AFCamEnt.GetMemoryPointPos(m_AFCamTo));
		vector dir = vector.Direction(eye, ahead).Normalized();
		if (!m_AFCam)
		{
			m_AFCam = Camera.Cast(GetGame().CreateObject("staticcamera", eye, true));
			m_AFCam.SetActive(true);
		}
		m_AFCam.SetPosition(eye);
		m_AFCam.LookAt(eye + dir * 20.0);
		m_AFCam.SetFOV(m_AFCamFov);
		Print("[AFTest] sight view " + name + " eye=" + eye.ToString() + " dir=" + dir.ToString());
	}

	void AFShotNamed(string name)
	{
		Print("[AFTest] screenshot " + name);
	}

	void AFIronView()
	{
		// 'eye' is the iron-sight camera; the bore runs from 'konec hlavne' to 'usti hlavne'.
		vector eye = g_AFHeld.GetMemoryPointPos("eye");
		vector a = g_AFHeld.GetMemoryPointPos("konec hlavne");
		vector b = g_AFHeld.GetMemoryPointPos("usti hlavne");
		Print("[AFTest] model eye=" + eye.ToString() + " barrel " + a.ToString() + " -> " + b.ToString());
		AFPointCam(g_AFHeld, "eye", "usti hlavne", 0.45, "sight_iron");
	}

	void AFFitScope()
	{
		EntityAI scope = g_AFHeld.GetInventory().CreateAttachment("AF_ZF4Optic");
		if (scope)
			Print("[AFTest] ZF4 fitted to the held rifle");
		else
			Print("[AFTest] FAILED to fit the ZF4 to the held rifle");
	}

	void AFScopeView()
	{
		EntityAI scope = g_AFHeld.FindAttachmentBySlotName("weaponOpticsAFStG");
		AFPointCam(scope, "eyescope", "cameradir", 0.30, "sight_scope");
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFScopeSide, 2500, false);
	}

	void AFScopeSide()
	{
		m_AFBurst = 1;
		m_AFBurstName = "scope_fitted";
		AFBurstStep();
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
