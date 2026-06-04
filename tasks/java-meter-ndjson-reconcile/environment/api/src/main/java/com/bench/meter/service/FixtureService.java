package com.bench.meter.service;

import com.bench.meter.config.MeterProperties;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class FixtureService {

    private static final String METER_ID = "MTR-2024-Q1";

    private final Path fixturesRoot;
    private final ObjectMapper objectMapper;
    private final Map<String, JsonNode> devices;
    private final List<JsonNode> corrections;

    public FixtureService(MeterProperties properties, ObjectMapper objectMapper) throws IOException {
        this.fixturesRoot = Path.of(properties.getFixturesDir());
        this.objectMapper = objectMapper;
        this.devices = loadDevices();
        this.corrections = loadCorrections();
    }

    public Optional<JsonNode> findDevice(String deviceId) {
        return Optional.ofNullable(devices.get(deviceId));
    }

    public List<JsonNode> correctionsForMeter(String meterId) {
        if (!METER_ID.equals(meterId)) {
            return List.of();
        }
        return corrections;
    }

    public Optional<ReadingPage> readingsPage(String meterId, String cursor) throws IOException {
        if (!METER_ID.equals(meterId)) {
            return Optional.empty();
        }
        if (cursor == null || cursor.isBlank()) {
            return Optional.of(new ReadingPage(readNdjson("readings_p0.ndjson"), "page1"));
        }
        if ("page1".equals(cursor)) {
            return Optional.of(new ReadingPage(readNdjson("readings_p1.ndjson"), null));
        }
        return Optional.empty();
    }

    private Map<String, JsonNode> loadDevices() throws IOException {
        Path path = fixturesRoot.resolve("devices.json");
        JsonNode root = objectMapper.readTree(Files.readString(path, StandardCharsets.UTF_8));
        return objectMapper.convertValue(root, new TypeReference<Map<String, JsonNode>>() {});
    }

    private List<JsonNode> loadCorrections() throws IOException {
        Path path = fixturesRoot.resolve("corrections.json");
        return objectMapper.readValue(
                Files.readString(path, StandardCharsets.UTF_8),
                new TypeReference<List<JsonNode>>() {});
    }

    private String readNdjson(String filename) throws IOException {
        return Files.readString(fixturesRoot.resolve(filename), StandardCharsets.UTF_8);
    }

    public record ReadingPage(String body, String nextCursor) {
    }
}
