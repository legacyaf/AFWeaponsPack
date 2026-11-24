// Script classes for the AF M107A1 and its built-in scope.
//
// AF_M107A1 behaves like the vanilla SVD (script class SVD_Base: its recoil, ironsight rules and
// handling), plus the server licence check from AFLicense.c, plus its scope: fitted when the rifle is
// made and never released.
//
// AF_M107Scope draws its own view while it is being looked through: the reticle (AF_Weapons/afm107/
// data/afm107_reticle_ca.paa, drawn from scratch), the magnification and a range readout measured
// to whatever is under the crosshair, every quarter second, as the vanilla rangefinder measures.

class AF_M107A1 : SVD_Base
{
	override void EEInit()
	{
		super.EEInit();

		if (GetGame().IsServer())
			GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(AF_FitScope, 200, false);

		if (GetGame().IsDedicatedServer())
		{
			AFLicense.Start();
			GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(AF_CheckLicense, 5000, false);
		}
	}

	//! The scope is part of the rifle: put it on if it is missing (new rifle, or one from an old save).
	void AF_FitScope()
	{
		if (!FindAttachmentBySlotName("weaponOpticsAFM107"))
			GetInventory().CreateAttachment("AF_M107Scope");
	}

	override bool CanReleaseAttachment(EntityAI attachment)
	{
		if (attachment && attachment.IsInherited(AF_M107Scope))
			return false;
		return super.CanReleaseAttachment(attachment);
	}

	//! Runs every 5 seconds until the licence is known. Deletes the weapon on an unlicensed server.
	void AF_CheckLicense()
	{
		if (AFLicense.IsOK())
			return;

		if (AFLicense.IsDenied())
		{
			GetGame().ObjectDelete(this);
			return;
		}

		AFLicense.Poll();
		GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(AF_CheckLicense, 5000, false);
	}

	//! Debug menu "Spawn Ground Special": with its magazine (the scope fits itself).
	override void OnDebugSpawn()
	{
		SpawnAttachedMagazine("Mag_AFM107_10Rnd");
	}
}

class AF_M107Scope : HuntingOptic
{
	static const string LAYOUT = "AF_Weapons/afm107/data/afm107_scope.layout";
	static const float MAX_RANGE = 2000;
	static ref array<int> MAGNIFICATION = {6, 8, 10, 12};

	protected Widget m_AFHud;
	protected ImageWidget m_AFReticle;
	protected ImageWidget m_AFSideLeft;
	protected ImageWidget m_AFSideRight;
	protected TextWidget m_AFRange;
	protected TextWidget m_AFZoom;
	protected float m_AFNextMeasure;

	override void EEInit()
	{
		super.EEInit();
		if (!GetGame().IsDedicatedServer())
			GetGame().GetCallQueue(CALL_CATEGORY_GUI).CallLater(AF_UpdateHud, 0, true);
	}

	override void EEDelete(EntityAI parent)
	{
		GetGame().GetCallQueue(CALL_CATEGORY_GUI).Remove(AF_UpdateHud);
		AF_HideHud();
		super.EEDelete(parent);
	}

	//! Every frame on a player's machine: show the view while this scope is looked through.
	void AF_UpdateHud()
	{
		if (!IsInOptics())
		{
			AF_HideHud();
			return;
		}
		if (!m_AFHud)
		{
			m_AFHud = GetGame().GetWorkspace().CreateWidgets(LAYOUT);
			if (!m_AFHud)
				return;
			m_AFReticle = ImageWidget.Cast(m_AFHud.FindAnyWidget("Reticle"));
			m_AFSideLeft = ImageWidget.Cast(m_AFHud.FindAnyWidget("SideLeft"));
			m_AFSideRight = ImageWidget.Cast(m_AFHud.FindAnyWidget("SideRight"));
			m_AFRange = TextWidget.Cast(m_AFHud.FindAnyWidget("Range"));
			m_AFZoom = TextWidget.Cast(m_AFHud.FindAnyWidget("Zoom"));
		}
		int sw, sh;
		GetScreenSize(sw, sh);
		// The round view fills the screen's height; black panels fill the sides beyond it.
		if (m_AFReticle)
			m_AFReticle.SetSize(sh, sh);
		float side = (sw - sh) * 0.5 + 2;
		if (m_AFSideLeft)
			m_AFSideLeft.SetSize(side, 1);
		if (m_AFSideRight)
			m_AFSideRight.SetSize(side, 1);
		m_AFHud.Show(true);

		int step = GetStepFOVIndex();
		if (m_AFZoom && step >= 0 && step < MAGNIFICATION.Count())
			m_AFZoom.SetText(MAGNIFICATION.Get(step).ToString() + "x");

		float now = GetGame().GetTickTime();
		if (now >= m_AFNextMeasure)
		{
			m_AFNextMeasure = now + 0.25;
			AF_Measure();
		}
	}

	//! Range to whatever is under the crosshair, from the aiming camera (as the vanilla rangefinder).
	void AF_Measure()
	{
		if (!m_AFRange)
			return;
		vector from = GetGame().GetCurrentCameraPosition();
		vector to = from + GetGame().GetCurrentCameraDirection() * MAX_RANGE;
		vector contact_pos, contact_dir;
		int component;
		bool hit = DayZPhysics.RaycastRV(from, to, contact_pos, contact_dir, component, null, null, GetGame().GetPlayer(), false, false, ObjIntersectIFire);
		if (!hit)
		{
			m_AFRange.SetText("RNG ---- m");
			return;
		}
		int metres = Math.Round(vector.Distance(from, contact_pos));
		string digits = metres.ToString();
		while (digits.Length() < 4)
			digits = "0" + digits;
		m_AFRange.SetText("RNG " + digits + " m");
	}

	void AF_HideHud()
	{
		if (m_AFHud)
			m_AFHud.Show(false);
	}
}
