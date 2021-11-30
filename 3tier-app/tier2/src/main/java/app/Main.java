package app;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.HashMap;
import java.util.concurrent.ExecutionException;

import com.google.common.net.InetAddresses;
import com.google.common.net.InternetDomainName;

import Server.SimpleTask;
import gnu.getopt.Getopt;
import gnu.getopt.LongOpt;
import jni.GetThreadID;
import kong.unirest.Unirest;
import net.spy.memcached.MemcachedClient;

public class Main {

	private static Boolean isEmu = false;
	private static String jedisHost = null;
	private static boolean cgv2 = false;

	public static void main(String[] args) {
		System.setProperty("net.spy.log.LoggerImpl", "net.spy.memcached.compat.log.SLF4JLogger");
		Unirest.config().concurrency(2000,2000);
		Main.getCliOptions(args);
		if (Main.cgv2) {
			Main.addToCgv2();
		}
		SimpleTask[] Sys = Main.genSystem();
		try {
			Main.resetState(Sys[0]);
		} catch (InterruptedException | ExecutionException e) {
			e.printStackTrace();
		}
		Sys[0].start();
	}

	public static void resetState(SimpleTask task) throws InterruptedException, ExecutionException {
		MemcachedClient memcachedClient = null;
		try {
			memcachedClient = new MemcachedClient(new InetSocketAddress(Main.jedisHost, 11211));
		} catch (IOException e) {
			e.printStackTrace();
		}

		memcachedClient.set(task.getName() + "_sw", 3600, "1").get();
		memcachedClient.set(task.getName() + "_hw", 3600, "1").get();
		String[] entries = task.getEntries().keySet().toArray(new String[0]);
		for (String e : entries) {
			memcachedClient.set(e + "_bl", 3600, "0").get();
			memcachedClient.set(e + "_ex", 3600, "0").get();
		}
		memcachedClient.shutdown();
	}

	public static SimpleTask[] genSystem() {
		// instatiate tier2 class
		HashMap<String, Class> t2Entries = new HashMap<String, Class>();
		HashMap<String, Long> t2Entries_stimes = new HashMap<String, Long>();
		t2Entries.put("e2", Tier2HTTPHandler.class);
		t2Entries_stimes.put("e2", 131l);
		final SimpleTask t2 = new SimpleTask("localhost", 3001, t2Entries, t2Entries_stimes, 1, Main.isEmu, "t2",
				Main.jedisHost, 100l, null, null, Main.cgv2);
		t2.setHwCore(1f);
		return new SimpleTask[] { t2 };
	}

	public static boolean validate(final String hostname) {
		return InetAddresses.isUriInetAddress(hostname) || InternetDomainName.isValid(hostname);
	}

	public static void addToCgv2() {
		try {
			int tid = GetThreadID.get_tid();
			// aggiungo questo thread al gruppo dei serventi del tier
			BufferedWriter out;
			try {
				out = new BufferedWriter(new FileWriter("/sys/fs/cgroup/t2/cgroup.procs", true));
				out.write(String.valueOf(tid));
				out.flush();
				out.close();
			} catch (IOException e) {
				e.printStackTrace();
			}
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	public static void getCliOptions(String[] args) {

		int c;
		LongOpt[] longopts = new LongOpt[3];
		longopts[0] = new LongOpt("cpuEmu", LongOpt.REQUIRED_ARGUMENT, null, 0);
		longopts[1] = new LongOpt("jedisHost", LongOpt.REQUIRED_ARGUMENT, null, 1);
		longopts[2] = new LongOpt("cgv2", LongOpt.REQUIRED_ARGUMENT, null, 2);

		Getopt g = new Getopt("ddctrl", args, "", longopts);
		g.setOpterr(true);
		while ((c = g.getopt()) != -1) {
			switch (c) {
			case 0:
				try {
					Main.isEmu = Integer.valueOf(g.getOptarg()) > 0 ? true : false;
				} catch (NumberFormatException e) {
					System.err.println(String.format("%s is not valid, it must be 0 or 1.", g.getOptarg()));
				}
				break;
			case 1:
				try {
					if (!Main.validate(g.getOptarg())) {
						throw new Exception(String.format("%s is not a valid jedis URL", g.getOptarg()));
					}
					Main.jedisHost = String.valueOf(g.getOptarg());
				} catch (Exception e) {
					e.printStackTrace();
				}
				break;
			case 2:
				try {
					Main.cgv2 = Integer.valueOf(g.getOptarg()) > 0 ? true : false;
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
