package app;

import java.io.IOException;
import java.io.OutputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpClient.Version;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;
import java.time.Duration;
import java.util.Map;

import com.google.common.collect.Maps;
import com.hubspot.jinjava.Jinjava;
import com.sun.net.httpserver.HttpExchange;

import Server.SimpleTask;
import Server.TierHttpHandler;
import jni.GetThreadID;

@SuppressWarnings("restriction")
public class Tier1HTTPHandler extends TierHttpHandler {

	private static String tier2Host = null;
	HttpClient client = null;

	public Tier1HTTPHandler(SimpleTask lqntask, HttpExchange req, long stime) {
		super(lqntask, req, stime);
		this.client = HttpClient.newBuilder().version(Version.HTTP_1_1).build();
	}

	public void handleResponse(HttpExchange req, String requestParamValue) throws InterruptedException, IOException {
		this.addToCGV2Group(this.getName());
		this.measureIngress();

		Jinjava jinjava = new Jinjava();
		Map<String, Object> context = Maps.newHashMap();
		context.put("task", "Tier1");
		context.put("entry", "e1");

		HttpRequest request = HttpRequest.newBuilder()
				.uri(URI.create("http://" + Tier1HTTPHandler.getTier2Host() + ":3001/?&entry=e2" + "&snd=" + this.getName()))
				.header("Connection", "close")
				.build();
		try {
			this.measureEgress();
			HttpResponse<String> resp = this.client.send(request, BodyHandlers.ofString());
			this.measureReturn();
		} catch (IOException e1) {
			e1.printStackTrace();
		} catch (InterruptedException e1) {
			e1.printStackTrace();
		}

		String renderedTemplate = jinjava.render(this.getWebPageTpl(), context);

		if (!this.getLqntask().isEmulated()) {
			this.doWorkCPU();
		} else {
			Float executing = 0f;
			String[] entries = this.getLqntask().getEntries().keySet().toArray(new String[0]);
			for (String e : entries) {
				executing += this.getLqntask().getState().get(e + "_ex").get();
			}
			this.doWorkSleep(executing);
		}

		this.measureEgress();

		req.getResponseHeaders().set("Content-Type", "text/html; charset=UTF-8");
		req.getResponseHeaders().set("Cache-Control", "no-store, no-cache, max-age=0, must-revalidate");
		OutputStream outputStream = req.getResponseBody();
		req.sendResponseHeaders(200, renderedTemplate.length());
		outputStream.write(renderedTemplate.getBytes());
		outputStream.flush();
		outputStream.close();
		outputStream = null;
	}

	@Override
	public String getWebPageName() {
		return "tier1.html";
	}

	@Override
	public String getName() {
		return "e1";
	}

	public static String getTier2Host() {
		return tier2Host;
	}

	public static void setTier2Host(String tier2Host) {
		Tier1HTTPHandler.tier2Host = tier2Host;
	}
}
