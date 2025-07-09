package ro.rasel.spring.microservices.passportservice.controller;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import ro.rasel.spring.microservices.passportservice.controller.dto.PassportResponse;

@OpenAPIDefinition(tags = @Tag(name = PassportApi.TAG, description = PassportApi.TAG + " REST controller"))
public interface PassportApi {

    String TAG = "passport";

    @Operation(summary = "Get passport", description = "Get passports", tags = TAG)
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "Found"),
            @ApiResponse(responseCode = "400", description = "Bad request"),
            @ApiResponse(responseCode = "404", description = "Not found"),
            @ApiResponse(responseCode = "500", description = "Internal server error")})
    @GetMapping(value = "/v1/users/{userId}/passport", produces = "application/json")
    ResponseEntity<PassportResponse> getPassport(@PathVariable String userId);
}
