// AF M107A1: a free offline session to try the rifle by hand (no script, no pictures, no auto-quit).
// Start it with: test\play_m107.ps1
// The player stands on the north-west airfield at noon with the M107A1 in hand (its scope fits itself),
// loaded, three spare magazines and a stack of .50 BMG rounds; a second rifle lies on the ground.

void main()
{
	GetGame().GetWorld().SetDate(2026, 6, 15, 12, 0);
	Weather weather = GetGame().GetWeather();
	weather.GetOvercast().Set(0, 0, 0);
	weather.GetRain().Set(0, 0, 0);
	weather.GetFog().Set(0, 0, 0);

	vector stand = "4660 0 10330";
	stand[1] = GetGame().SurfaceY(stand[0], stand[2]);
	PlayerBase player = PlayerBase.Cast(GetGame().CreatePlayer(NULL, "SurvivorM_Mirek", stand, 0, "NONE"));
	GetGame().SelectPlayer(NULL, player);
	player.GetInventory().CreateInInventory("TShirt_Green");
	player.GetInventory().CreateInInventory("CargoPants_Green");
	player.GetInventory().CreateInInventory("AthleticShoes_Green");
	player.GetInventory().CreateInInventory("HighCapacityVest_Olive");
	player.GetInventory().CreateInInventory("Mag_AFM107_10Rnd");
	player.GetInventory().CreateInInventory("Mag_AFM107_10Rnd");
	player.GetInventory().CreateInInventory("Ammo_AF50BMG");

	Weapon_Base held = Weapon_Base.Cast(player.GetHumanInventory().CreateInHands("AF_M107A1"));
	if (held)
		held.SpawnAmmo("Mag_AFM107_10Rnd", WeaponWithAmmoFlags.CHAMBER | WeaponWithAmmoFlags.MAX_CAPACITY_MAG);
	GetGame().CreateObject("AF_M107A1", Vector(stand[0] + 1.5, stand[1], stand[2] + 1.0), false);
	Print("[AFPlay] ready");
}

class CustomMission: MissionGameplay
{
};

Mission CreateCustomMission(string path)
{
	return new CustomMission();
}
