// Allied Forces Weapons Pack - server licence check.
//
// On a dedicated server, the first AF weapon that is created asks the Allied Forces
// website whether this server (the IP the request comes from + the game port) is on
// the whitelist. Until the answer is "AF_OK", AF weapons are deleted shortly after
// they are created. No answer, an error or a timeout all count as "not licensed".
//
// The website side lives in licensing/supabase (table af_server_whitelist).
// Single-player / offline missions are not checked.

class AFLicenseCallback : RestCallback
{
	override void OnError(int errorCode)
	{
		AFLicense.OnFailed("error " + errorCode.ToString());
	}

	override void OnTimeout()
	{
		AFLicense.OnFailed("timeout");
	}

	override void OnSuccess(string data, int dataSize)
	{
		AFLicense.OnAnswer(data);
	}
}

class AFLicense
{
	static const string URL = "https://kbifstvpqputwqtalyxz.supabase.co/functions/v1/";
	static const int PENDING = 0;
	static const int OK = 1;
	static const int DENIED = 2;
	static const int MAX_TRIES = 3;			// website unreachable: try this many times, then deny
	static const int GIVE_UP_MS = 120000;	// no answer at all after this long: deny

	protected static int s_State;
	protected static bool s_Started;
	protected static bool s_RetryDue;
	protected static int s_Tries;
	protected static int s_StartTime;
	protected static ref AFLicenseCallback s_Callback;

	static bool IsOK()
	{
		return s_State == OK;
	}

	static bool IsDenied()
	{
		return s_State == DENIED;
	}

	//! Called by every AF weapon on a dedicated server. Only the first call does anything.
	static void Start()
	{
		if (s_Started)
			return;

		s_Started = true;
		s_StartTime = GetGame().GetTime();
		Request();
	}

	//! Called by the weapons while they wait: retries a failed request and enforces the time limit.
	static void Poll()
	{
		if (s_State != PENDING)
			return;

		if (GetGame().GetTime() - s_StartTime > GIVE_UP_MS)
		{
			Deny("no answer from the licence server");
			return;
		}

		if (s_RetryDue)
		{
			s_RetryDue = false;
			Request();
		}
	}

	protected static void Request()
	{
		s_Tries++;

		string port;
		if (!GetGame().CommandlineGetParam("port", port) || port == "")
			port = "2302";

		RestApi api = GetRestApi();
		if (!api)
			api = CreateRestApi();

		if (!api)
		{
			OnFailed("REST API not available");
			return;
		}

		if (!s_Callback)
			s_Callback = new AFLicenseCallback();

		RestContext ctx = api.GetRestContext(URL);
		ctx.GET(s_Callback, "af-license?port=" + port);
	}

	static void OnAnswer(string data)
	{
		if (s_State != PENDING)
			return;

		if (data.Contains("AF_OK"))
		{
			s_State = OK;
			Print("[AF_Weapons] Server licence OK.");
			return;
		}

		Deny("this server is not on the Allied Forces whitelist");
	}

	static void OnFailed(string why)
	{
		if (s_State != PENDING)
			return;

		if (s_Tries < MAX_TRIES)
		{
			Print("[AF_Weapons] Licence check failed (" + why + "), trying again.");
			s_RetryDue = true;
			return;
		}

		Deny("licence server unreachable (" + why + ")");
	}

	protected static void Deny(string why)
	{
		s_State = DENIED;
		Print("[AF_Weapons] NOT LICENSED: " + why + ". Allied Forces weapons are disabled on this server.");
	}
}
