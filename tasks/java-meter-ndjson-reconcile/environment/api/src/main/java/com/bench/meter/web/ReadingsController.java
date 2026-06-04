package com.bench.meter.web;

import com.bench.meter.service.FixtureService;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/readings")
public class ReadingsController {

    private final FixtureService fixtureService;

    public ReadingsController(FixtureService fixtureService) {
        this.fixtureService = fixtureService;
    }

    @GetMapping(value = "/stream", produces = "application/x-ndjson")
    public ResponseEntity<String> stream(
            @RequestParam String meterId,
            @RequestParam(defaultValue = "") String cursor) throws Exception {
        return fixtureService.readingsPage(meterId, cursor)
                .map(page -> {
                    ResponseEntity.BodyBuilder builder = ResponseEntity.ok()
                            .contentType(MediaType.parseMediaType("application/x-ndjson"));
                    if (page.nextCursor() != null) {
                        builder.header("X-Next-Cursor", page.nextCursor());
                    }
                    return builder.body(page.body());
                })
                .orElse(ResponseEntity.notFound().build());
    }
}
