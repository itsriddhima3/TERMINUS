package com.bench.meter.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "meter")
public class MeterProperties {

    private String fixturesDir = "fixtures";

    public String getFixturesDir() {
        return fixturesDir;
    }

    public void setFixturesDir(String fixturesDir) {
        this.fixturesDir = fixturesDir;
    }
}
