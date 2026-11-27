// The PeaceKeeper's iron-sight camera.
//
// The vanilla iron-sight camera cuts away everything nearer than 4 cm (its near plane). The PeaceKeeper's
// rear sight base starts 3.5 cm in front of the eye, so the cut opened its rear end and the rifle showed
// through the bottom of the sight (owner 2026-11-27). With the PeaceKeeper's own sights in use the near
// plane is 1.5 cm, so the whole sight is drawn. Other weapons, and optics on the PeaceKeeper, are unchanged.

modded class DayZPlayerCameraIronsights
{
	static const float AF_PK_NEARPLANE = 0.015;

	override void OnUpdate(float pDt, out DayZPlayerCameraResult pOutResult)
	{
		super.OnUpdate(pDt, pOutResult);

		if (m_weaponUsed && !m_opticsUsed && m_weaponUsed.IsInherited(AF_PeaceKeeper))
			pOutResult.m_fNearPlane = AF_PK_NEARPLANE;
	}
}
