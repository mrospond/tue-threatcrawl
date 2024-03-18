const config = require('../config.json');
const { MongoClient, GridFSBucket, ObjectID } = require('mongodb');

/**
 * Class to initiate database connection
 */
class Connection {
    async connect() {
        try {
            if (this.client !== undefined) {
                return;
            }

            const uri = `mongodb://${config['username']}:${config['password']}@${config['host']}:${config['port']}/${config['authorization_database']}`;

            this.client = MongoClient(uri, { useUnifiedTopology: true });
            await this.client.connect();

            this.bucket = new GridFSBucket(this.db);
        } catch (exception) {
            console.error('Could not connect to the database:');
            throw exception;
        }
    }

    get db() {
        return this.client.db('THREATcrawl');
    }

    retrieveFile(objectId) {
        objectId = ObjectID(objectId);

        return new Promise((resolve, reject) => {
            const buffers = [];

            this.bucket.openDownloadStream(objectId)
                .on('data', buffer => buffers.push(buffer))
                .on('end', () => resolve(Buffer.concat(buffers)));
        });
    }
}

const connection = new Connection();

module.exports = connection;
