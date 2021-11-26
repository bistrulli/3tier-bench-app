package app;

import java.io.IOException;
import java.io.OutputStream;
import java.util.Map;

import com.google.common.collect.Maps;
import com.hubspot.jinjava.Jinjava;
import com.sun.net.httpserver.HttpExchange;

import Server.SimpleTask;
import Server.TierHttpHandler;

@SuppressWarnings("restriction")
public class Tier2HTTPHandler extends TierHttpHandler {

	public Tier2HTTPHandler(SimpleTask lqntask, HttpExchange req, long stime) {
		super(lqntask, req, stime);
	}

	public void handleResponse(HttpExchange req, String requestParamValue) throws InterruptedException, IOException {
		this.addToCGV2Group(this.getName());
		this.measureIngress();

		Jinjava jinjava = new Jinjava();
		Map<String, Object> context = Maps.newHashMap();
		context.put("task", "Tier2");
		context.put("entry", "e2");

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
		return "tier2.html";
	}

	@Override
	public String getName() {
		return "e2";
	}
}
