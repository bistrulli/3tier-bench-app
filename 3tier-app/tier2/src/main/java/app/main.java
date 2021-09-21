package app;

import java.util.HashMap;

import com.google.common.net.InetAddresses;
import com.google.common.net.InternetDomainName;

import Server.SimpleTask;
import gnu.getopt.Getopt;
import gnu.getopt.LongOpt;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.Transaction;

public class main {

	private static Boolean isEmu = false;
	private static String jedisHost = null;

	public static void main(String[] args) {
		main.getCliOptions(args);
		SimpleTask[] Sys = main.genSystem();
		main.resetState(Sys[0]);
		Sys[0].start();
	}

	public static void resetState(SimpleTask task) {
		Jedis jedis = new Jedis("localhost");
		Transaction t = jedis.multi();
		String[] entries = task.getEntries().keySet().toArray(new String[0]);
		for (String e : entries) {
			t.set(e + "_bl", "0");
			t.set(e + "_ex", "0");
		}
		t.exec();
		t.close();
		jedis.close();
	}

	public static SimpleTask[] genSystem() {
		// instatiate tier2 class
		HashMap<String, Class> t2Entries = new HashMap<String, Class>();
		HashMap<String, Long> t2Entries_stimes = new HashMap<String, Long>();
		t2Entries.put("e2", Tier2HTTPHandler.class);
		t2Entries_stimes.put("e2", 100l);
		final SimpleTask t2 = new SimpleTask("localhost", 3001, t2Entries, t2Entries_stimes, 1, main.isEmu, "t2",
				main.jedisHost);
		t2.setHwCore(1f);
		return new SimpleTask[] { t2 };
	}
	
	public static boolean validate(final String hostname) {
        return InetAddresses.isUriInetAddress(hostname) || 
        		InternetDomainName.isValid(hostname);
    }

	public static void getCliOptions(String[] args) {

		int c;
		LongOpt[] longopts = new LongOpt[2];
		longopts[0] = new LongOpt("cpuEmu", LongOpt.REQUIRED_ARGUMENT, null, 0);
		longopts[1] = new LongOpt("jedisHost", LongOpt.REQUIRED_ARGUMENT, null, 1);

		Getopt g = new Getopt("ddctrl", args, "", longopts);
		g.setOpterr(true);
		while ((c = g.getopt()) != -1) {
			switch (c) {
			case 0:
				try {
					main.isEmu = Integer.valueOf(g.getOptarg()) > 0 ? true : false;
				} catch (NumberFormatException e) {
					System.err.println(String.format("%s is not valid, it must be 0 or 1.", g.getOptarg()));
				}
				break;
			case 1:
				try {
					if (!main.validate(g.getOptarg())) {
						throw new Exception(String.format("%s is not a valid jedis URL", g.getOptarg()));
					}
					main.jedisHost = String.valueOf(g.getOptarg());
				} catch (Exception e) {
					e.printStackTrace();
				}
				break;
			default:
				break;
			}
		}
	}

}
