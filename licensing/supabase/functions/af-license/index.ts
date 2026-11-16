// Allied Forces Weapons Pack - server licence check (Supabase Edge Function).
// This is the code deployed as "af-license" in the AlliedForces Supabase project:
//   https://kbifstvpqputwqtalyxz.supabase.co/functions/v1/af-license?port=2302
//
// A DayZ server running the mod calls it with its game port. The function looks at the
// IP the call came from plus that port and answers in plain text:
//   AF_OK       this ip:port is in af_server_whitelist and enabled
//   AF_DENIED   it is not
// The mod treats anything other than AF_OK, including no answer, as "not licensed".
//
// "Verify JWT" must be OFF for this function (Edge Functions > af-license > Settings):
// a DayZ server cannot send an API key header.
// Tables: ../../migrations/af_server_whitelist.sql
import { createClient } from "npm:@supabase/supabase-js@2";

const text = (body: string, status = 200) =>
  new Response(body, {
    status,
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" },
  });

Deno.serve(async (req) => {
  try {
    const url = new URL(req.url);
    const port = Number.parseInt(url.searchParams.get("port") ?? "", 10);
    // Supabase puts the real caller first in x-forwarded-for.
    const ip = (req.headers.get("x-forwarded-for") ?? "").split(",")[0].trim();
    if (!ip || !Number.isInteger(port) || port < 1 || port > 65535) {
      return text("AF_DENIED");
    }
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    );
    const { data, error } = await supabase
      .from("af_server_whitelist")
      .select("id")
      .eq("ip", ip)
      .eq("port", port)
      .eq("enabled", true)
      .limit(1);
    if (error) console.error("whitelist lookup failed", error.message);
    const allowed = !error && (data?.length ?? 0) > 0;
    // Keep a trail of who asked, so unlicensed servers show up in the database.
    const log = await supabase.from("af_license_checks").insert({ ip, port, allowed });
    if (log.error) console.error("check log failed", log.error.message);
    return text(allowed ? "AF_OK" : "AF_DENIED");
  } catch (e) {
    console.error("af-license error", e);
    return text("AF_DENIED");
  }
});
