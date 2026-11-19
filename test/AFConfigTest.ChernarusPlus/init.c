// Offline check of the server settings (AFConfig.c). Runs only in DayZDiag_x64.exe on this PC.
// Start it with: test\run_test.ps1 -Mission AFConfigTest.ChernarusPlus -TimeoutSeconds 120
//
// It prints the settings that were loaded from test\profiles\AF_WeaponsPack.json and, for every
// weapon of the pack, the recoil, sway and jam values the game ends up with, so a change in the
// file can be compared against the script log. It also reports which weapons were removed
// because the file disables them. Lines start with "[AFCfg]".

ref array<EntityAI> g_AFItems = new array<EntityAI>;
ref TStringArray g_AFNames = new TStringArray;

void main()
{
	GetGame().GetWorld().SetDate(2026, 6, 15, 12, 0);
	vector pos = "4660 0 10330";
	pos[1] = GetGame().SurfaceY(pos[0], pos[2]);
	PlayerBase player = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", pos, 0, "NONE"));
	GetGame().SelectPlayer(NULL, player);

	AFConfigData data = AFConfig.Get();
	Print("[AFCfg] EnableSettings=" + data.EnableSettings.ToString() + " globalRecoil=" + data.GlobalRecoilMultiplier.ToString() + " globalSway=" + data.GlobalSwayMultiplier.ToString() + " globalDamage=" + data.GlobalDamageMultiplier.ToString() + " immune=" + data.WeaponsImmuneToBulletDamage.ToString() + " weapons=" + data.Weapons.Count().ToString());

	TStringArray types = {"AF7_Vanguard", "AF7_Vanguard_Gold", "AFM41_Pathfinder", "AF_MP40", "AF_P08", "AF_P08_Gold", "M4A1", "UMP45"};
	for (int i = 0; i < types.Count(); i++)
	{
		vector p = Vector(pos[0] + 2 + i, pos[1], pos[2]);
		EntityAI item = EntityAI.Cast(GetGame().CreateObjectEx(types.Get(i), p, ECE_PLACE_ON_SURFACE));
		g_AFItems.Insert(item);
		g_AFNames.Insert(types.Get(i));
		Weapon_Base w = Weapon_Base.Cast(item);
		if (!w)
		{
			Print("[AFCfg] FAILED to spawn " + types.Get(i));
			continue;
		}
		AFWeaponSettings s = AFConfig.For(w);
		if (i == 0)
			AFKitTest(player, pos);
		string own = "none (not a weapon of the pack)";
		if (s)
			own = "file entry " + s.ClassName + " enabled=" + s.Enabled.ToString() + " recoil=" + s.RecoilMultiplier.ToString() + " sway=" + s.SwayMultiplier.ToString() + " damage=" + s.DamageMultiplier.ToString() + " jam=" + s.JamChanceMultiplier.ToString() + " wear=" + s.ExtraWearPerShot.ToString();
		PropertyModifiers pm = w.GetPropertyModifierObject();
		Print("[AFCfg] " + types.Get(i) + ": " + own + " | recoilModifier=" + pm.m_RecoilModifiers.ToString() + " swayModifier=" + pm.m_SwayModifiers.ToString());
	}
}

// The repair kit, without the crafting animation: a ruined P08 and a fresh kit, used until the kit is gone.
void AFKitTest(PlayerBase player, vector pos)
{
	ItemBase gun = ItemBase.Cast(GetGame().CreateObjectEx("AF_P08", Vector(pos[0], pos[1], pos[2] + 2), ECE_PLACE_ON_SURFACE));
	ItemBase kit = ItemBase.Cast(GetGame().CreateObjectEx("AF_WeaponRepairKit", Vector(pos[0] + 0.5, pos[1], pos[2] + 2), ECE_PLACE_ON_SURFACE));
	ItemBase other = ItemBase.Cast(GetGame().CreateObjectEx("M4A1", Vector(pos[0] + 1.0, pos[1], pos[2] + 2), ECE_PLACE_ON_SURFACE));
	if (!gun || !kit || !other)
	{
		Print("[AFCfg] kit test FAILED to spawn its items");
		return;
	}
	gun.SetHealth01("", "", 0.0);
	other.SetHealth01("", "", 0.3);
	AFRepairWeapon recipe = new AFRepairWeapon;
	ItemBase wrong[2];
	wrong[0] = kit;
	wrong[1] = other;
	Print("[AFCfg] kit: quantity " + kit.GetQuantity().ToString() + " of " + kit.GetQuantityMax().ToString() + ", seconds " + recipe.GetLengthInSecs().ToString() + ", can repair an M4A1: " + recipe.CanDo(wrong, player).ToString());
	ItemBase pair[2];
	pair[0] = kit;
	pair[1] = gun;
	for (int i = 1; i <= 6; i++)
	{
		if (!kit)
		{
			Print("[AFCfg] kit: used up after " + (i - 1).ToString() + " uses");
			break;
		}
		gun.SetHealth01("", "", 0.0);
		bool can = recipe.CanDo(pair, player);
		recipe.Do(pair, player, null, 0);
		string left = "gone";
		if (kit && !kit.IsSetForDeletion())
			left = kit.GetQuantity().ToString();
		else
			kit = null;
		Print("[AFCfg] kit use " + i.ToString() + ": could repair a ruined P08: " + can.ToString() + ", P08 health now " + gun.GetHealth01("", "").ToString() + ", kit left " + left);
	}
}

class CustomMission: MissionGameplay
{
	override void OnInit()
	{
		super.OnInit();
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(this.AFReport, 9000, false);
	}

	void AFReport()
	{
		for (int i = 0; i < g_AFItems.Count(); i++)
		{
			string state = "still there";
			if (!g_AFItems.Get(i))
				state = "REMOVED";
			Print("[AFCfg] after 9 s: " + g_AFNames.Get(i) + " " + state);
		}
		Print("[AFCfg] done");
		GetGame().RequestExit(0);
	}
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
