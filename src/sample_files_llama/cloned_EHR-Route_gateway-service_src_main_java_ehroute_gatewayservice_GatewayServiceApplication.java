package ehroute.gatewayservice;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.cloud.netflix.eureka.EnableEurekaClient;
import org.springframework.context.annotation.Bean;


@SpringBootApplication
@EnableEurekaClient
public class GatewayServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(GatewayServiceApplication.class, args);
	}

	@Bean
	public RouteLocator appRoutes(RouteLocatorBuilder builder) {
		return builder.routes()
			.route(r -> r
				.path("/config/**")
				.uri("lb://config-server")
				.id("ConfigServer"))
			.route(r -> r
				.path("/provider/**")
				.uri("lb://provider-service")
				.id("ProviderService"))
			.route(r -> r
				.path("/patient/**")
				.uri("lb://patient-service")
				.id("PatientService"))
			.route(r -> r
				.path("/identity/**")
				.uri("lb://identity-service")
				.id("IdentityService"))
		.build();
	}

}
