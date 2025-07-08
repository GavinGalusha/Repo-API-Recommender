package org.dicegroup.basilisk.repositoryService.web.controllers.repo;

import com.fasterxml.jackson.annotation.JsonView;
import com.sun.istack.NotNull;
import org.dicegroup.basilisk.dto.Views;
import org.dicegroup.basilisk.dto.repo.DockerRepoDto;
import org.dicegroup.basilisk.repositoryService.model.benchmarking.TripleStore;
import org.dicegroup.basilisk.repositoryService.model.repo.docker.DockerRepo;
import org.dicegroup.basilisk.repositoryService.services.benchmarking.TripleStoreService;
import org.dicegroup.basilisk.repositoryService.services.repo.DockerRepoService;
import org.modelmapper.ModelMapper;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;


@RestController
@RequestMapping("repos/docker")
public class DockerRepoController {

    private final DockerRepoService repoService;
    private final TripleStoreService tsService;
    private final ModelMapper modelMapper;

    public DockerRepoController(DockerRepoService repoService, TripleStoreService tsService, ModelMapper mapper) {
        this.repoService = repoService;
        this.tsService = tsService;
        this.modelMapper = mapper;
    }

    @GetMapping
    @JsonView(Views.Api.class)
    public ResponseEntity<List<DockerRepoDto>> getAllRepos() {
        List<DockerRepoDto> repoDtoList = convertToDtoList(this.repoService.getAllRepos());
        return new ResponseEntity<>(repoDtoList, HttpStatus.OK);
    }

    @PostMapping(consumes = "application/json", produces = "application/json")
    public ResponseEntity<DockerRepoDto> addRepo(@RequestBody @NotNull DockerRepoDto repoDto) {
        DockerRepo repo = convertToEntity(repoDto);
        if (repoDto.getTripleStore() != null && repoDto.getTripleStore().getId() != null) {
            Optional<TripleStore> tsOptional = this.tsService.getTripleStore(repoDto.getTripleStore().getId());
            tsOptional.ifPresent(repo::setTripleStore);
        }

        DockerRepo createdRepo = this.repoService.addRepo(repo);
        return new ResponseEntity<>(convertToDto(createdRepo), HttpStatus.CREATED);
    }

    @DeleteMapping(path = "/{id}")
    public ResponseEntity<String> deleteRepo(@PathVariable @NotNull Long id) {
        Optional<DockerRepo> repo = this.repoService.getRepo(id);
        if (repo.isPresent()) {
            this.repoService.deleteRepo(repo.get());
            return new ResponseEntity<>("The Docker repository has been removed.", HttpStatus.OK);
        } else {
            return new ResponseEntity<>("There is no Docker repository with ID " + id, HttpStatus.OK);
        }
    }

    private List<DockerRepoDto> convertToDtoList(List<DockerRepo> repos) {
        return repos.stream().map(this::convertToDto).collect(Collectors.toList());
    }

    private DockerRepoDto convertToDto(DockerRepo repo) {
        return this.modelMapper.map(repo, DockerRepoDto.class);
    }

    private DockerRepo convertToEntity(DockerRepoDto repoDto) {
        return this.modelMapper.map(repoDto, DockerRepo.class);
    }
}
