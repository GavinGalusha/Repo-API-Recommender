package org.dicegroup.basilisk.repositoryService.model.benchmarking;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.experimental.SuperBuilder;
import org.dicegroup.basilisk.repositoryService.model.repo.docker.DockerRepo;

import javax.persistence.Entity;
import javax.persistence.ManyToOne;


@Setter
@Getter
@SuperBuilder
@Entity
@NoArgsConstructor
public class DockerBenchmarkJob extends BenchmarkJob {

    @ManyToOne
    private DockerRepo repo;

    private String tagName;

    private String imageDigest;

}
