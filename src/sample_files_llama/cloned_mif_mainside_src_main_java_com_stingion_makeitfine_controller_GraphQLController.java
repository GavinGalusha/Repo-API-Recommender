/*
 *  Created under not commercial project "Make it fine"
 *
 *  Copyright 2017-2021
 *  @author stingion
 */

package com.stingion.makeitfine.controller;

import graphql.ExecutionResult;
import graphql.GraphQL;
import graphql.schema.GraphQLSchema;
import io.swagger.annotations.Api;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("gql")
@Api(tags = {"GraphQLController"})
public class GraphQLController {

    private GraphQL graphQL;

    public GraphQLController(GraphQLSchema graphQLSchema) {
        graphQL = GraphQL.newGraphQL(graphQLSchema).build();
    }

    @PostMapping
    public ResponseEntity<Object> listDepartments(@RequestBody String query) {
        ExecutionResult execute = graphQL.execute(query);
        return new ResponseEntity<>(execute, HttpStatus.OK);
    }
}
