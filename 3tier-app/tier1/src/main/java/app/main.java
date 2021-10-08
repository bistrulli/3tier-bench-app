package app;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.HashMap;

import com.google.common.net.InetAddresses;
import com.google.common.net.InternetDomainName;

import Server.SimpleTask;
import gnu.getopt.Getopt;
import gnu.getopt.LongOpt;
import net.spy.memcached.MemcachedClient;

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
		MemcachedClient memcachedClient=null;
		try {
			memcachedClient = new MemcachedClient(new InetSocketAddress(main.jedisHost, 11211));
		} catch (IOException e) {
			e.printStackTrace();
		}
		String[] entries = task.getEntries().keySet().toArray(new String[0]);
		for (String e : entries) {
			memcachedClient.set(e + "_bl",Integer.MAX_VALUE, "0");
			memcachedClient.set(e + "_ex",Integer.MAX_VALUE,"0");
		}
		memcachedClient.shutdown();
	}

	public static SimpleTask[] genSystem() {
		// instatiate tier2 class
		HashMap<String, Class> t1Entries = new HashMap<String, Class>();
		HashMap<String, Long> t1Entries_stimes = new HashMap<String, Long>();
		t1Entries.put("e1", Tier1HTTPHandler.class);
		t1Entries_stimes.put("e1", 100l);
		final SimpleTask t1 = new SimpleTask("localhost", 3000, t1Entries, t1Entries_stimes, 1, main.isEmu, "t1",
				main.jedisHost);
		t1.setHwCore(1f);
		return new SimpleTask[] { t1 };
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
						throw new Exception(String.format("%s is not a valid jedis HOST", g.getOptarg()));
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
