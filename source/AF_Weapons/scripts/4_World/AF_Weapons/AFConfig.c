// Allied Forces Weapons Pack - server settings.
//
// A server owner tunes the pack's weapons in one file in the server's profiles folder:
//
//     <profiles>\AF_WeaponsPack.json
//
// The file is written with default values the first time the server starts, and rewritten on
// every start so that settings and weapons added by a newer version of the mod appear in it.
// The server sends its settings to every player when they join, because recoil and sway are
// worked out on the player's own PC.
//
// The settings only ever touch weapons of this pack (AFConfig.BASE_CLASSES and everything that
// inherits from them). Vanilla weapons and other mods' weapons are never changed.
//
// What cannot be a setting: fire rate, magazine size, ammunition and attachment slots are fixed
// in config.cpp when the mod is built.

//! Settings for one weapon. ClassName is the standard finish; its other finishes follow it.
class AFWeaponSettings
{
	string ClassName;
	bool Enabled = true;                //!< false: the weapon is removed wherever it appears
	float RecoilMultiplier = 1.0;       //!< 0.5 = half the recoil, 2.0 = twice
	float SwayMultiplier = 1.0;         //!< 0.5 = half the sway
	float DamageMultiplier = 1.0;       //!< applies to players, infected and animals hit with this weapon
	float JamChanceMultiplier = 1.0;    //!< 0 = never jams
	float ExtraWearPerShot = 0.0;       //!< health points the weapon loses per shot, on top of the game's own wear

	void AFWeaponSettings(string className = "")
	{
		ClassName = className;
	}
}

//! The whole file.
class AFConfigData
{
	int ConfigVersion = 1;
	bool EnableSettings = true;                    //!< false: everything below is ignored, the weapons behave as built
	float GlobalRecoilMultiplier = 1.0;            //!< every weapon of the pack; multiplied with the weapon's own value
	float GlobalSwayMultiplier = 1.0;
	float GlobalDamageMultiplier = 1.0;
	float GlobalJamChanceMultiplier = 1.0;
	bool WeaponsImmuneToBulletDamage = false;      //!< true: a bullet hitting a weapon of the pack does not damage it

	// Weapon repair kit (item AF_WeaponRepairKit): drag it onto a weapon of the pack.
	bool RepairKitEnabled = true;
	float RepairKitSeconds = 8.0;                  //!< how long one repair takes
	float RepairKitHealthAdd = 1.0;                //!< share of full health one use restores: 1.0 = back to pristine, 0.25 = a quarter
	int RepairKitUses = 4;                         //!< uses in one kit
	bool RepairKitRepairsRuined = true;            //!< false: a ruined weapon stays ruined
	bool RepairKitWorksOnSuppressors = false;      //!< true: also repairs suppressors (any suppressor, they are vanilla items)

	// Sounds other players can hear when a weapon of the pack is aimed, zoomed or zeroed.
	bool AimSoundsEnabled = true;
	float AimSoundRadius = 10.0;                   //!< metres; players further away are not sent the sound
	string AimSoundSetRifle = "Weapon_Movement_Rifle_walkRasErc_SoundSet";
	string AimSoundSetPistol = "Weapon_Movement_Pistol_walkRasErc_SoundSet";
	string ZeroSoundSet = "combinationlock_changedial_SoundSet";
	string ZoomSoundSet = "Fire_Mode_Switch_Simple_Click_SoundSet";
	ref array<ref AFWeaponSettings> Weapons = new array<ref AFWeaponSettings>;
}

class AFConfig
{
	static const string FILE = "$profile:AF_WeaponsPack.json";
	static const int RPC_REQUEST = 0x41460001;     //!< player -> server: send me the settings
	static const int RPC_SETTINGS = 0x41460002;    //!< server -> player: the settings, as JSON text
	static const int RPC_SOUND = 0x41460003;       //!< player -> server: I aimed / zoomed / zeroed
	static const int RPC_SOUND_PLAY = 0x41460004;  //!< server -> players nearby: play that sound on this player
	static const int SOUND_AIM = 0;
	static const int SOUND_ZERO = 1;
	static const int SOUND_ZOOM = 2;
	static const float MAX_MULTIPLIER = 10.0;

	//! One entry per weapon of the pack: the class of its standard finish.
	static ref TStringArray BASE_CLASSES = {"AF7_Vanguard", "AFM41_Pathfinder", "AF_MP40", "AF_P08"};

	protected static ref AFConfigData s_Data;
	protected static bool s_Loaded;          //!< server / single player: the file has been read
	protected static bool s_Received;        //!< player: the server's settings have arrived
	protected static int s_LastRequest;
	protected static int s_Revision;         //!< goes up whenever the settings change; weapons re-read theirs
	static bool s_ApplyingDamage;            //!< guard: our own scaled damage must not be scaled again

	static int GetRevision()
	{
		return s_Revision;
	}

	//! The settings in force, never null. On a player's PC these are the defaults until the server's arrive.
	static AFConfigData Get()
	{
		if (!s_Data)
		{
			if (!GetGame().IsMultiplayer() || GetGame().IsDedicatedServer())
				Load();
			else
				s_Data = Defaults();
		}
		return s_Data;
	}

	static AFConfigData Defaults()
	{
		AFConfigData data = new AFConfigData;
		foreach (string name : BASE_CLASSES)
			data.Weapons.Insert(new AFWeaponSettings(name));
		return data;
	}

	protected static float Clamp(float value)
	{
		return Math.Clamp(value, 0.0, MAX_MULTIPLIER);
	}

	//! Fills in what is missing and keeps every value in a sane range.
	protected static void Tidy(AFConfigData data)
	{
		if (!data.Weapons)
			data.Weapons = new array<ref AFWeaponSettings>;
		foreach (string name : BASE_CLASSES)
		{
			bool found = false;
			foreach (AFWeaponSettings have : data.Weapons)
			{
				if (have && have.ClassName == name)
					found = true;
			}
			if (!found)
				data.Weapons.Insert(new AFWeaponSettings(name));
		}
		data.GlobalRecoilMultiplier = Clamp(data.GlobalRecoilMultiplier);
		data.GlobalSwayMultiplier = Clamp(data.GlobalSwayMultiplier);
		data.GlobalDamageMultiplier = Clamp(data.GlobalDamageMultiplier);
		data.GlobalJamChanceMultiplier = Clamp(data.GlobalJamChanceMultiplier);
		data.RepairKitSeconds = Math.Clamp(data.RepairKitSeconds, 1.0, 120.0);
		data.RepairKitHealthAdd = Math.Clamp(data.RepairKitHealthAdd, 0.01, 1.0);
		data.RepairKitUses = Math.Clamp(data.RepairKitUses, 1, 100);
		data.AimSoundRadius = Math.Clamp(data.AimSoundRadius, 0.0, 100.0);
		foreach (AFWeaponSettings w : data.Weapons)
		{
			if (!w)
				continue;
			w.RecoilMultiplier = Clamp(w.RecoilMultiplier);
			w.SwayMultiplier = Clamp(w.SwayMultiplier);
			w.DamageMultiplier = Clamp(w.DamageMultiplier);
			w.JamChanceMultiplier = Clamp(w.JamChanceMultiplier);
			w.ExtraWearPerShot = Math.Clamp(w.ExtraWearPerShot, 0.0, 1000.0);
		}
		data.ConfigVersion = 1;
	}

	//! Server and single player: read the file (or write a new one with the defaults).
	static void Load()
	{
		AFConfigData data;
		if (FileExist(FILE))
		{
			JsonFileLoader<AFConfigData>.JsonLoadFile(FILE, data);
			if (!data)
			{
				Print("[AF_WeaponsPack] " + FILE + " could not be read (check the commas and brackets). Using the defaults; the file was left as it is.");
				s_Data = Defaults();
				s_Loaded = true;
				s_Revision++;
				return;
			}
		}
		else
		{
			data = Defaults();
		}
		Tidy(data);
		JsonFileLoader<AFConfigData>.JsonSaveFile(FILE, data);
		s_Data = data;
		s_Loaded = true;
		s_Revision++;
		Print("[AF_WeaponsPack] settings loaded from " + FILE + ", " + data.Weapons.Count().ToString() + " weapons");
	}

	//! Is this one of the pack's weapons? Returns the class its settings are filed under, or "".
	static string BaseClassOf(EntityAI weapon)
	{
		if (!weapon)
			return "";
		foreach (string name : BASE_CLASSES)
		{
			if (weapon.IsKindOf(name))
				return name;
		}
		return "";
	}

	//! Settings for a weapon of the pack; null for any other weapon, or when the settings are switched off.
	static AFWeaponSettings For(EntityAI weapon)
	{
		string name = BaseClassOf(weapon);
		if (name == "")
			return null;
		AFConfigData data = Get();
		if (!data.EnableSettings)
			return null;
		foreach (AFWeaponSettings w : data.Weapons)
		{
			if (w && w.ClassName == name)
				return w;
		}
		return null;
	}

	// ------------------------------------------------------------------ sending to players

	//! Player's PC: ask the server for its settings (at most once every 10 seconds until they arrive).
	static void RequestFromServer()
	{
		if (!GetGame().IsMultiplayer() || GetGame().IsDedicatedServer() || s_Received)
			return;
		int now = GetGame().GetTime();
		if (s_LastRequest != 0 && now - s_LastRequest < 10000)
			return;
		Man player = GetGame().GetPlayer();
		if (!player)
			return;
		s_LastRequest = now;
		ScriptRPC rpc = new ScriptRPC();
		rpc.Send(player, RPC_REQUEST, true, null);
	}

	//! Server: a player asked.
	static void SendTo(Man player, PlayerIdentity identity)
	{
		if (!player || !identity)
			return;
		string json = JsonFileLoader<AFConfigData>.JsonMakeData(Get());
		ScriptRPC rpc = new ScriptRPC();
		rpc.Write(json);
		rpc.Send(player, RPC_SETTINGS, true, identity);
	}

	//! Player's PC: the server's settings arrived.
	static void Receive(ParamsReadContext ctx)
	{
		string json;
		if (!ctx.Read(json))
			return;
		AFConfigData data;
		JsonFileLoader<AFConfigData>.JsonLoadData(json, data);
		if (!data)
			return;
		Tidy(data);
		s_Data = data;
		s_Received = true;
		s_Revision++;
		// The weapon in the player's hands worked out its recoil and sway before the settings came.
		PlayerBase player = PlayerBase.Cast(GetGame().GetPlayer());
		if (player)
		{
			Weapon_Base weapon = Weapon_Base.Cast(player.GetItemInHands());
			if (weapon && weapon.GetPropertyModifierObject())
				weapon.GetPropertyModifierObject().UpdateModifiers();
		}
	}

	// ------------------------------------------------------------------ sounds

	//! The sound set for one of the three events, "" for none.
	static string SoundSetFor(int type, EntityAI weapon)
	{
		AFConfigData data = Get();
		if (!data.EnableSettings || !data.AimSoundsEnabled)
			return "";
		if (type == SOUND_ZERO)
			return data.ZeroSoundSet;
		if (type == SOUND_ZOOM)
			return data.ZoomSoundSet;
		if (weapon && weapon.IsKindOf("Pistol_Base"))
			return data.AimSoundSetPistol;
		return data.AimSoundSetRifle;
	}

	//! Any PC: play the sound on a player.
	static void PlayOn(PlayerBase player, int type)
	{
		if (!player || GetGame().IsDedicatedServer())
			return;
		string name = SoundSetFor(type, player.GetItemInHands());
		if (name == "")
			return;
		EffectSound sound = SEffectManager.PlaySoundOnObject(name, player);
		if (sound)
			sound.SetAutodestroy(true);
	}

	//! Server: a player aimed, zoomed or zeroed. Tell the players within earshot.
	static void RelaySound(PlayerBase source, int type)
	{
		if (!source || type < SOUND_AIM || type > SOUND_ZOOM)
			return;
		if (BaseClassOf(source.GetItemInHands()) == "" || SoundSetFor(type, source.GetItemInHands()) == "")
			return;
		float radius = Get().AimSoundRadius;
		array<Man> players = new array<Man>;
		GetGame().GetPlayers(players);
		foreach (Man other : players)
		{
			if (!other || other == source || !other.GetIdentity())
				continue;
			if (vector.Distance(other.GetPosition(), source.GetPosition()) > radius)
				continue;
			ScriptRPC rpc = new ScriptRPC();
			rpc.Write(type);
			rpc.Send(source, RPC_SOUND_PLAY, true, other.GetIdentity());
		}
	}

	// ------------------------------------------------------------------ damage

	//! Called for a player, infected or animal about to take damage, on the server. Returns false when
	//! the hit was applied here instead, scaled by the weapon's damage setting.
	static bool OnDamage(EntityAI victim, int damageType, EntityAI source, string dmgZone, string ammo, vector modelPos)
	{
		if (s_ApplyingDamage || damageType != DamageType.FIRE_ARM || !source || !GetGame().IsServer())
			return true;
		AFWeaponSettings w = For(source);
		if (!w)
			return true;
		float scale = w.DamageMultiplier * Get().GlobalDamageMultiplier;
		if (scale > 0.999 && scale < 1.001)
			return true;
		if (scale > 0.0)
		{
			s_ApplyingDamage = true;
			victim.ProcessDirectDamage(damageType, source, dmgZone, ammo, modelPos, scale);
			s_ApplyingDamage = false;
		}
		return false;
	}
}

// ---------------------------------------------------------------------- recoil and sway

modded class PropertyModifiers
{
	override void UpdateModifiers()
	{
		super.UpdateModifiers();
		AFConfig.RequestFromServer();
		AFWeaponSettings w = AFConfig.For(m_OwnerItem);
		if (!w)
			return;
		AFConfigData data = AFConfig.Get();
		float recoil = w.RecoilMultiplier * data.GlobalRecoilMultiplier;
		float sway = w.SwayMultiplier * data.GlobalSwayMultiplier;
		m_RecoilModifiers = m_RecoilModifiers * recoil;
		// Sway: the first two numbers are how fast and how far the weapon wanders; the third is a speed, left alone.
		m_SwayModifiers[0] = m_SwayModifiers[0] * sway;
		m_SwayModifiers[1] = m_SwayModifiers[1] * sway;
	}
}

// ---------------------------------------------------------------------- the weapons themselves

modded class Weapon_Base
{
	protected int m_AFRevision = -1;

	//! Recoil and sway are worked out when attachments change. Work them out again if the settings changed since.
	protected void AF_Refresh()
	{
		if (m_AFRevision == AFConfig.GetRevision())
			return;
		m_AFRevision = AFConfig.GetRevision();
		if (GetPropertyModifierObject())
			GetPropertyModifierObject().UpdateModifiers();
	}

	override void EEInit()
	{
		super.EEInit();
		if (GetGame().IsServer() && AFConfig.BaseClassOf(this) != "")
			GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(AF_RemoveIfDisabled, 3000, false);
	}

	void AF_RemoveIfDisabled()
	{
		AFWeaponSettings w = AFConfig.For(this);
		if (w && !w.Enabled)
			GetGame().ObjectDelete(this);
	}

	//! The jam roll. The game adds the magazine's own jam chance in several weapon base classes, so the
	//! multiplier is applied here, to the final chance. Same random number as the game's own roll, so the
	//! player's PC and the server stay in step.
	override bool JamCheck(int muzzleIndex)
	{
		AFWeaponSettings w = AFConfig.For(this);
		if (!w)
			return super.JamCheck(muzzleIndex);
		PlayerBase player = PlayerBase.Cast(GetHierarchyRootPlayer());
		if (!player)
			return false;
		float rnd = player.GetRandomGeneratorSyncManager().GetRandom01(RandomGeneratorSyncUsage.RGSJam);
		float chance = Math.Clamp(GetSyncChanceToJam() * w.JamChanceMultiplier * AFConfig.Get().GlobalJamChanceMultiplier, 0.0, 1.0);
		return rnd < chance;
	}
	override void EEFired(int muzzleType, int mode, string ammoType)
	{
		super.EEFired(muzzleType, mode, ammoType);
		AFWeaponSettings w = AFConfig.For(this);
		if (!w)
			return;
		AF_Refresh();
		if (GetGame().IsServer() && w.ExtraWearPerShot > 0.0)
			AddHealth("", "Health", -w.ExtraWearPerShot);
	}

	override bool EEOnDamageCalculated(TotalDamageResult damageResult, int damageType, EntityAI source, int component, string dmgZone, string ammo, vector modelPos, float speedCoef)
	{
		if (damageType == DamageType.FIRE_ARM && AFConfig.BaseClassOf(this) != "")
		{
			AFConfigData data = AFConfig.Get();
			if (data.EnableSettings && data.WeaponsImmuneToBulletDamage)
				return false;
		}
		return super.EEOnDamageCalculated(damageResult, damageType, source, component, dmgZone, ammo, modelPos, speedCoef);
	}
}

// ---------------------------------------------------------------------- who gets hit

modded class PlayerBase
{
	protected EntityAI m_AFSoundWeapon;
	protected bool m_AFWasAiming;
	protected float m_AFZeroing;
	protected int m_AFZoom;
	protected int m_AFLastSoundTime;

	//! On the PC of the player holding the weapon: notice aiming, zeroing and zooming, and make the sound.
	override void CommandHandler(float pDt, int pCurrentCommandID, bool pCurrentCommandFinished)
	{
		super.CommandHandler(pDt, pCurrentCommandID, pCurrentCommandFinished);
		if (GetGame().IsDedicatedServer() || PlayerBase.Cast(GetGame().GetPlayer()) != this)
			return;
		Weapon_Base weapon = Weapon_Base.Cast(GetItemInHands());
		if (weapon && AFConfig.BaseClassOf(weapon) == "")
			weapon = null;
		bool aiming = false;
		float zeroing = 0;
		int zoom = -1;
		if (weapon)
		{
			aiming = IsInIronsights() || IsInOptics();
			zeroing = weapon.GetCurrentZeroing(weapon.GetCurrentMuzzle());
			ItemOptics optic = weapon.GetAttachedOptics();
			if (optic)
				zoom = optic.GetStepFOVIndex();
		}
		if (weapon && weapon == m_AFSoundWeapon)
		{
			if (aiming && !m_AFWasAiming)
				AF_Sound(AFConfig.SOUND_AIM);
			if (zeroing != m_AFZeroing)
				AF_Sound(AFConfig.SOUND_ZERO);
			if (zoom != m_AFZoom && zoom >= 0 && m_AFZoom >= 0)
				AF_Sound(AFConfig.SOUND_ZOOM);
		}
		m_AFSoundWeapon = weapon;
		m_AFWasAiming = aiming;
		m_AFZeroing = zeroing;
		m_AFZoom = zoom;
	}

	protected void AF_Sound(int type)
	{
		AFConfig.PlayOn(this, type);
		if (GetGame().IsMultiplayer())
		{
			ScriptRPC rpc = new ScriptRPC();
			rpc.Write(type);
			rpc.Send(this, AFConfig.RPC_SOUND, true, null);
		}
	}

	override void OnPlayerLoaded()
	{
		super.OnPlayerLoaded();
		AFConfig.RequestFromServer();
	}

	override void OnRPC(PlayerIdentity sender, int rpc_type, ParamsReadContext ctx)
	{
		super.OnRPC(sender, rpc_type, ctx);
		if (rpc_type == AFConfig.RPC_REQUEST)
		{
			if (GetGame().IsServer() && sender)
				AFConfig.SendTo(this, sender);
		}
		else if (rpc_type == AFConfig.RPC_SETTINGS)
		{
			if (!GetGame().IsDedicatedServer())
				AFConfig.Receive(ctx);
		}
		else if (rpc_type == AFConfig.RPC_SOUND)
		{
			// Only from the player themself, and not more than ten a second.
			int type;
			int now = GetGame().GetTime();
			if (GetGame().IsServer() && sender && GetIdentity() && sender.GetId() == GetIdentity().GetId() && now - m_AFLastSoundTime > 100 && ctx.Read(type))
			{
				m_AFLastSoundTime = now;
				AFConfig.RelaySound(this, type);
			}
		}
		else if (rpc_type == AFConfig.RPC_SOUND_PLAY)
		{
			int heard;
			if (!GetGame().IsDedicatedServer() && ctx.Read(heard))
				AFConfig.PlayOn(this, heard);
		}
	}

	override bool EEOnDamageCalculated(TotalDamageResult damageResult, int damageType, EntityAI source, int component, string dmgZone, string ammo, vector modelPos, float speedCoef)
	{
		if (!AFConfig.OnDamage(this, damageType, source, dmgZone, ammo, modelPos))
			return false;
		return super.EEOnDamageCalculated(damageResult, damageType, source, component, dmgZone, ammo, modelPos, speedCoef);
	}
}

modded class ZombieBase
{
	override bool EEOnDamageCalculated(TotalDamageResult damageResult, int damageType, EntityAI source, int component, string dmgZone, string ammo, vector modelPos, float speedCoef)
	{
		if (!AFConfig.OnDamage(this, damageType, source, dmgZone, ammo, modelPos))
			return false;
		return super.EEOnDamageCalculated(damageResult, damageType, source, component, dmgZone, ammo, modelPos, speedCoef);
	}
}

modded class AnimalBase
{
	override bool EEOnDamageCalculated(TotalDamageResult damageResult, int damageType, EntityAI source, int component, string dmgZone, string ammo, vector modelPos, float speedCoef)
	{
		if (!AFConfig.OnDamage(this, damageType, source, dmgZone, ammo, modelPos))
			return false;
		return super.EEOnDamageCalculated(damageResult, damageType, source, component, dmgZone, ammo, modelPos, speedCoef);
	}
}
