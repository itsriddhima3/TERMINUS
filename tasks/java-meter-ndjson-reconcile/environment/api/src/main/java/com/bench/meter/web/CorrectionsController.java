package com.bench.meter.web;

import com.bench.meter.service.FixtureService;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/corrections")
public class CorrectionsController {

    private final FixtureService fixtureService;

    public CorrectionsController(FixtureService fixtureService) {
        this.fixtureService = fixtureService;
    }

    @GetMapping
    public List<JsonNode> corrections(@RequestParam String meterId) {
        return fixtureService.correctionsForMeter(meterId);
    }
}
