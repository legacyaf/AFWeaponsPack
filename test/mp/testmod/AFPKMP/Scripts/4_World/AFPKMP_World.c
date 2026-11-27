// Test-only. See config.cpp.
modded class AF_PeaceKeeper
{
	//! The count on the round counter's display (-1: "--", -2: not set yet).
	int AFT_Shown()
	{
		return m_AFShown;
	}

	//! This PC is not a licensed server: keep the rifle so its mechanics can be tested.
	override void AF_CheckLicense()
	{
	}
}
