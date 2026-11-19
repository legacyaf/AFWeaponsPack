// Allied Forces Weapons Pack - weapon repair kit.
//
// The item AF_WeaponRepairKit (config.cpp) repairs a weapon of this pack when it is combined with
// it, like the game's own cleaning kit: kit in the hands and the weapon in front of you or in the
// inventory, or the other way round. How long it takes, how much it restores, how many uses a kit
// has, whether it brings a ruined weapon back and whether it also works on suppressors are all
// settings in AF_WeaponsPack.json (see AFConfig.c and docs/SETTINGS.md).

class AFRepairWeapon : RecipeBase
{
	override void Init()
	{
		m_Name = "Repair weapon";
		m_IsInstaRecipe = false;
		m_AnimationLength = 2;          // not used: GetLengthInSecs below reads the setting
		m_Specialty = -0.02;

		// No damage or quantity limits here; CanDo decides (the game's own limits would refuse a ruined weapon).
		m_MinDamageIngredient[0] = -1;
		m_MaxDamageIngredient[0] = -1;
		m_MinQuantityIngredient[0] = -1;
		m_MaxQuantityIngredient[0] = -1;
		m_MinDamageIngredient[1] = -1;
		m_MaxDamageIngredient[1] = -1;
		m_MinQuantityIngredient[1] = -1;
		m_MaxQuantityIngredient[1] = -1;

		InsertIngredient(0, "AF_WeaponRepairKit");
		m_IngredientAddHealth[0] = 0;
		m_IngredientSetHealth[0] = -1;
		m_IngredientAddQuantity[0] = 0;
		m_IngredientDestroy[0] = false;
		m_IngredientUseSoftSkills[0] = false;

		foreach (string name : AFConfig.BASE_CLASSES)
			InsertIngredient(1, name, DayZPlayerConstants.CMD_ACTIONFB_CLEANING_WEAPON, true);
		InsertIngredient(1, "ItemSuppressor");
		m_IngredientAddHealth[1] = 0;
		m_IngredientSetHealth[1] = -1;
		m_IngredientAddQuantity[1] = 0;
		m_IngredientDestroy[1] = false;
		m_IngredientUseSoftSkills[1] = false;
	}

	override float GetLengthInSecs()
	{
		return AFConfig.Get().RepairKitSeconds;
	}

	override bool CanDo(ItemBase ingredients[], PlayerBase player)
	{
		AFConfigData data = AFConfig.Get();
		if (!data.EnableSettings || !data.RepairKitEnabled)
			return false;
		ItemBase target = ingredients[1];
		if (!target)
			return false;
		if (target.IsKindOf("ItemSuppressor"))
		{
			if (!data.RepairKitWorksOnSuppressors)
				return false;
		}
		else if (AFConfig.BaseClassOf(target) == "")
		{
			return false;
		}
		if (target.IsRuined() && !data.RepairKitRepairsRuined)
			return false;
		return target.GetHealth01("", "") < 0.999;
	}

	override void Do(ItemBase ingredients[], PlayerBase player, array<ItemBase> results, float specialty_weight)
	{
		AFConfigData data = AFConfig.Get();
		ItemBase kit = ingredients[0];
		ItemBase target = ingredients[1];
		if (!kit || !target)
			return;
		target.SetHealth01("", "", Math.Clamp(target.GetHealth01("", "") + data.RepairKitHealthAdd, 0.0, 1.0));
		float left = kit.GetQuantity() - kit.GetQuantityMax() / data.RepairKitUses;
		if (left < 0.5)
			GetGame().ObjectDelete(kit);
		else
			kit.SetQuantity(left);
	}
}

modded class PluginRecipesManagerBase
{
	override void RegisterRecipies()
	{
		super.RegisterRecipies();
		RegisterRecipe(new AFRepairWeapon);
	}
}
