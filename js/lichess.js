"use strict";

const Engine = require('node-uci').Engine;
const axios = require('axios');

const engine = new Engine('/home/keunwoo/Documents/Projects/chess-engine/mcts.py');

//engine.chain()
//.init()
//.isready()
//.position('startpos')
//.go({movetime: 10000})
//.then(result => {
    //console.log(result);
//})
//.catch(error => {
    //console.log(error);
//});


class LichessClient {
    constructor(username, password) {
        this.username = username || '';
        this.password = password || '';
    }
    login() {
        if (!this.username || !this.password) {
            throw new Error('Cannot login. Username or password not set');
        }
        axios.post('https://lichess.org/login', {
            username: this.username,
            password: this.password,
        }, {
            headers: {
                'Accept': 'application/vnd.lichess.v1+json'
            }
        })
        .then(function(response) {
            this.cookie = response.headers['set-cookie'].split(';', 1)[0];
            console.log('Login successful');
        })
        .catch(function (error) {
            throw error;
        });
    }
}

const c = new LichessClient('yureka123', 'L8YI0i$OeSd^9ZT%S@');
c.login();
