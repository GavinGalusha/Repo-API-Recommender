import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { NGXLogger } from 'ngx-logger';
import { Observable, of, BehaviorSubject } from 'rxjs';
import { catchError, map, tap, concatMap, filter } from 'rxjs/operators';
import { IdCid, IdToPath, Content, Reputation, reviver, FileRefs, replacer, WebSite } from '../_models';
import { RespWithLink, User, Relation, Auth } from '../_models';
import { Config } from '../config';

export interface IdParams {
  [name: string]: string;
}

interface TextResponseOption {
  headers?: HttpHeaders | {
    [header: string]: string | string[];
  };
  observe: 'response';
  params?: HttpParams | {
    [param: string]: string | string[];
  };
  reportProgress?: boolean;
  responseType: 'text';
  withCredentials?: boolean;
}

const writeOptions: TextResponseOption = {
  headers: new HttpHeaders({ 'Content-Type': 'application/json' }),
  observe: 'response',
  responseType: 'text'
};

const baseOptions: TextResponseOption = {
  observe: 'response',
  responseType: 'text'
};

@Injectable({
  providedIn: 'root'
})
export class BackendService {

  private userSubject: BehaviorSubject<User>;

  private relationSubject: BehaviorSubject<Relation>;

  private webSite: WebSite;

  constructor(
    private http: HttpClient,
    private logger: NGXLogger) {

    this.userSubject = new BehaviorSubject<User>(User.guest());
    this.relationSubject = new BehaviorSubject<Relation>(Relation.empty);
  }

  getWebSite(): Observable<WebSite> {
    if (this.webSite) {
      return of(this.webSite);
    }

    return this.getModel<WebSite>(WebSite, Config.webSite.identity).pipe(
      tap(webSite => this.webSite = webSite)
    );
  }

  getUserValue(): User {
    return this.userSubject.getValue();
  }

  getUser(identity?: string): Observable<User> {
    if (identity) { // request other user for inquery
      return this.getModel<User>(User, identity);
    } else {
      return this.userSubject;
    }
  }

  changeUser(username?: string): Observable<User> {
    this.logger.trace("changeUser, username:", username);
    if (username) {
      return this.getModel<User>(User, null, 'un', username).pipe(
        tap(user => this.userSubject.next(user)),
        concatMap(user => this.getModel<Relation>(Relation, user.identity)),
        tap(relation => this.relationSubject.next(relation)),
        map(_ => this.userSubject.value)
      );
    } else {
      this.userSubject.next(User.guest());
      this.relationSubject.next(Relation.empty);
      return of(this.userSubject.value);
    }
  }

  signUpUser(user: User): Observable<User> {
    return this.http.post(encodeURI(Config.signupUrl), JSON.stringify(user, replacer), writeOptions).pipe(
      map(resp => JSON.parse(resp.body, reviver)),
      map(object => Object.assign(new User, object)),
      tap(item => this.logger.trace('signUp User:', item)),
    );
  }

  postUser(user: User): Observable<User> {
    return this.postModel<User>(User, user).pipe(
      tap(user => this.userSubject.next(user))
    );
  }

  getRelation(): Observable<Relation> {
    return this.relationSubject;
  }

  postRelation(follow:boolean, followerId: string, followeeId: string): Observable<Relation> {

    if (this.userSubject.value.isGuest()) {
      this.logger.warn("Guest user's postRelation request is ignored");
      return of(this.relationSubject.value);
    }

    let url = Config.relationUrl + (follow ? Config.path.follow : Config.path.unfollow)
        + "/" + followerId + "/" + followeeId;

    return this.http.post(encodeURI(url), null, writeOptions).pipe(
      map(resp => JSON.parse(resp.body, reviver)),
      map(object => Object.assign(new Relation(), object)),
      tap(relation => this.relationSubject.next(relation)),
      tap(relation => this.logger.trace('postRelation resp:', relation))
    );
  }

  getPopularItems<T>(type, containerId: string): Observable<T[]> {

    let url = Config.getUrl(type) + Config.path.popular + '?cid=' + containerId;

    return this.http.get(encodeURI(url), baseOptions).pipe(
      map(resp => JSON.parse(resp.body, reviver)),
      map(array => array.map(object => Object.assign(new type(), object))),
      tap(items => this.logger.trace('getPopularItems resp:', items)),
      catchError(this.handleError('getPopularItems', []))
    );
  }

  getSearch(nextInfo: string, tag?: string, page?: string, size?: string)
      : Observable<RespWithLink<Content>> {

    page = page ? page : Config.paging.defaultPage;
    size = size ? size: Config.paging.defaultSize;

    let queryParams: string = nextInfo ? nextInfo : `?tag=${tag}&page=${page}&size=${size}`;

    return this.http.get(encodeURI(Config.searchUrl + queryParams), baseOptions).pipe(
      map(resp => RespWithLink.of<Content>(
        JSON.parse(resp.body, reviver).map(object => Object.assign(new Content(), object)),
        resp.headers.get("link")
      )),
      tap(items => this.logger.trace('getSearch resp:', items)),
      catchError(this.handleError<RespWithLink<Content>>(`getSearch query:${queryParams}`))
    );
  }

  getModels<T>(type, nextInfo: string, params: IdParams, page?: string, size?: string)
      : Observable<RespWithLink<T>> {

    page = page ? page : Config.paging.defaultPage;
    size = size ? size: Config.paging.defaultSize;

    let queryParams: string = nextInfo ? nextInfo
        : '?' + Object.keys(params).map(key => key + '=' + params[key]).join('&') + `&page=${page}&size=${size}`;

    return this.http.get(encodeURI(Config.getUrl(type) + queryParams) , baseOptions).pipe(
      map(resp => RespWithLink.of<T>(
        JSON.parse(resp.body, reviver).map(object => Object.assign(new type(), object)),
        resp.headers.get("link")
      )),
      tap(items => this.logger.trace('getModels resp:', items)),
      catchError(this.handleError<RespWithLink<T>>(`getModels query:${queryParams}`))
    );
  }

  getModel<T>(type, idToPath?: IdToPath, queryName?: string, queryValue?: string): Observable<T> {
    let url = Config.getUrl(type)
        + (idToPath ? '/' + idToPath.toString() : '')
        + (queryName && queryValue ? '?' + queryName + '=' + queryValue : '');

    return this.http.get(encodeURI(url), baseOptions).pipe(
      map(resp => JSON.parse(resp.body, reviver)),
      map(object => Object.assign(new type(), object)),
      tap(item => this.logger.trace('getModel resp:', item)),
      catchError(this.handleError<T>(`getModel model=${type.name} idToPath=${idToPath}`))
    );
  }

  postModel<T>(type, entity: T, urlSuffix?: string): Observable<T> {
    let url = Config.getUrl(type) + (urlSuffix ? '/' + urlSuffix : '');

    return this.http.post(encodeURI(url), JSON.stringify(entity, replacer), writeOptions).pipe(
      map(resp => JSON.parse(resp.body, reviver)),
      map(object => Object.assign(new type(), object)),
      tap(item => this.logger.trace('postModel resp:', item)),
      catchError(this.handleError<T>('postModel'))
    );
  }

  deleteModel(type, idToPath: IdToPath, urlSuffix?: string): Observable<any> {
    let url = Config.getUrl(type) + '/' + idToPath.toString() + (urlSuffix ? '/' + urlSuffix : '');

    return this.http.delete(encodeURI(url), writeOptions).pipe(
      tap(resp => this.logger.trace(`deleteModel idToPath:${idToPath}, resp:`, resp)),
      catchError(this.handleError<string>('deleteModel'))
    );
  }

  // FileList contains only one element when identity is used.
  // identity is the same as user identity, it enable to find the user picture by user id.
  addFile(identity: string, file: FileList): Observable<FileRefs> {
    let uploadData = new FormData();
    uploadData.append('attachment', file[0], file[0].name);

    let url = Config.fileUrl + '/' + identity;

    return this.http.post(encodeURI(url), uploadData, baseOptions).pipe(
      map(resp => JSON.parse(resp.body, reviver)),
      map(object => Object.assign(new FileRefs(), object)),
      tap(item => this.logger.trace('addFile resp:', item)),
      catchError(this.handleError<FileRefs>('addFile'))
    );
  }

  addFiles(files: FileList): Observable<FileRefs[]> {
    let uploadData = new FormData();

    for (let i = 0; i < files.length; i++) {
      uploadData.append('attachment', files[i], files[i].name);
    }

    return this.http.post(encodeURI(Config.fileUrl), uploadData, baseOptions).pipe(
      map(resp => JSON.parse(resp.body, reviver)),
      map(array => array.map(object => Object.assign(new FileRefs(), object))),
      tap(items => this.logger.trace('addFiles resp:', items)),
      catchError(this.handleError<FileRefs[]>('addFiles', []))
    );
  }

  deleteFiles(files: FileRefs[]): Observable<any> {
    return this.http.post(encodeURI(Config.fileDeletesUrl), JSON.stringify(files, replacer), writeOptions).pipe(
      tap(resp => this.logger.trace('deleteFiles resp:', resp)),
      catchError(this.handleError<FileRefs[]>('deleteFiles'))
    );
  }

  acculateRepute(typeName: string, idCid: IdCid, reputation: Reputation): Observable<Reputation> {
    let rpt = Object.assign(new Reputation(), reputation);
    rpt.idCid = idCid;

    let url = Config.getUrl(Config.toRptName(typeName));

    return this.http.post(encodeURI(url), JSON.stringify(rpt, replacer), writeOptions).pipe(
      map(resp => JSON.parse(resp.body, reviver)),
      map(object => Object.assign(new Reputation(), object)),
      tap(item => this.logger.trace('acculateRepute resp:', item)),
      catchError(this.handleError<Reputation>('acculateRepute'))
    );
  }

  authorize(username: string, password: string): Observable<Auth> {
    let httpHeaders = new HttpHeaders()
        .set('Authorization', 'Basic ' + window.btoa(Config.auth.clientId + ':' + Config.auth.clientPass));

    let url = `${Config.authUrl}?grant_type=password&username=${username}&password=${password}`;

    return this.http.post<Auth>(encodeURI(url), null, {headers: httpHeaders});
  }

  /**
   * Handle Http operation that failed.
   * Let the app continue.
   * @param operation - name of the operation that failed
   * @param result - optional value to return as the observable result
   */
  private handleError<T>(operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {

      // send the error to remote logging infrastructure
      this.logger.error(operation, error);

      // Let the app keep running by returning an empty result.
      return of(result as T);
    };
  }
}
