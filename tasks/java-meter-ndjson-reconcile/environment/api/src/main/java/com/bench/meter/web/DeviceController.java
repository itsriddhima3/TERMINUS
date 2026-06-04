package com.bench.meter.web;

import com.bench.meter.service.FixtureService;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/devices")
public class DeviceController {

    private final FixtureService fixtureService;

    public DeviceController(FixtureService fixtureService) {
        this.fixtureService = fixtureService;
    }

    @GetMapping("/{deviceId}")
    public ResponseEntity<JsonNode> device(@PathVariable String deviceId) {
        return fixtureService.findDevice(deviceId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
