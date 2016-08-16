from . import db


class AtlasDB(db.Model):
    __tablename__ = 'atlas'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = db.Column(db.Integer, primary_key=True)
    nodes = db.Column(db.SmallInteger, nullable=False)
    edges = db.Column(db.SmallInteger, nullable=False)
    name = db.Column(db.String(30), nullable=False, unique=True)
    two_core_id = db.Column(db.Integer, db.ForeignKey('atlas.id', ondelete='CASCADE'))
    graphs = db.relationship('GraphDB', back_populates='atlas')
    two_core = db.relationship('AtlasDB', cascade='all, delete-orphan', passive_deletes=True)

    def __repr__(self):
        return '<AtlasDB(name={0}, nodes={1}, edges={2})>'.format(self.name, self.nodes, self.edges)


class CutoffDB(db.Model):
    __tablename__ = 'cutoff'
    __table_args__ = (db.UniqueConstraint('scut', 'kcut'), {'mysql_engine': 'InnoDB'})
    id = db.Column(db.Integer, primary_key=True)
    scut = db.Column(db.Numeric(4, 2), nullable=False)
    kcut = db.Column(db.Integer, nullable=False)
    graphs = db.relationship('GraphDB', back_populates='cutoff')

    def __repr__(self):
        return '<CutoffDB(scut={0}, kcut={1})>'.format(self.scut, self.kcut)


class GraphDB(db.Model):
    __tablename__ = 'graph'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    connected_component = db.Column(db.SmallInteger, nullable=False, index=True)
    atlas_id = db.Column(db.ForeignKey('atlas.id'), index=True, nullable=False)
    cutoff_id = db.Column(db.ForeignKey('cutoff.id'), nullable=False, index=True)
    pdbe_id = db.Column(db.ForeignKey('pdbe.id', ondelete='CASCADE'), nullable=False, index=True)

    atlas = db.relationship('AtlasDB', back_populates='graphs')
    cutoff = db.relationship('CutoffDB', back_populates='graphs')
    pdbe = db.relationship('PdbeDB', back_populates='graphs')

    def __repr__(self):
        return '<GraphDB(pdb={0}, name={1})>'.format(self.pdbe.pdb.pdb, self.atlas.name)


class PdbDB(db.Model):
    __tablename__ = 'pdb'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    pdb = db.Column(db.String(4), nullable=False, unique=True)

    cdhit_full = db.relationship('CdhitFullDB', back_populates='pdb', cascade='all, delete-orphan', passive_deletes=True)
    pdbes = db.relationship('PdbeDB', back_populates='pdb', cascade='all, delete-orphan', passive_deletes=True)

    def __repr__(self):
        return '<PdbDB(pdb={0})>'.format(self.pdb)


class PdbeDB(db.Model):
    __tablename__ = 'pdbe'
    __table_args__ = (db.UniqueConstraint('pdb_id', 'mmol'), {'mysql_engine': 'InnoDB'})

    id = db.Column(db.Integer, primary_key=True)
    # specific mysql data type, maximum value = 255.
    mmol = db.Column(db.SmallInteger, nullable=False)
    preferred = db.Column(db.Boolean, nullable=False, index=True)
    pdb_id = db.Column(db.ForeignKey('pdb.id', ondelete='CASCADE'), nullable=False, index=True)

    pdb = db.relationship('PdbDB', back_populates='pdbes')
    graphs = db.relationship('GraphDB', back_populates='pdbe', cascade='all, delete-orphan', passive_deletes=True)

    def __repr__(self):
        return '<PdbeDB(pdb={0}, mmol={1}, preferred={2})>'.format(self.pdb.pdb, self.mmol, bool(self.preferred))


class CdhitFullDB(db.Model):
    __tablename__ = 'cdhit_full'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    c90 = db.Column(db.Boolean, default=False)
    c80 = db.Column(db.Boolean, default=False)
    c70 = db.Column(db.Boolean, default=False)
    c60 = db.Column(db.Boolean, default=False)
    pdb_id = db.Column(db.ForeignKey('pdb.id', ondelete='CASCADE'), nullable=False, index=True)

    pdb = db.relationship('PdbDB', back_populates='cdhit_full')

    def __repr__(self):
        return '<CdhitFullDB(pdb={0}, c90={1})>'.format(self.pdb.pdb, self.c90)